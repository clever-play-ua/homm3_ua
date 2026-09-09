"""
Minimal Smacker (.smk) container + audio-only decoder, ported from
libsmacker (https://github.com/JonnyH/libsmacker, C, public domain-ish /
zlib-like license). ffmpeg's own smackaudio decoder produces pure noise for
these HoMM3 files (verified by spectrogram) - this reimplements the
reference algorithm faithfully instead of guessing at a fix.

Only extracts audio (track 0). Video huffman trees are skipped wholesale
(we don't need to decode video - ffmpeg already does that part correctly).
"""
import struct
import wave


class BitReader:
    __slots__ = ("bit", "data", "end", "pos")
    def __init__(self, data, offset=0):
        self.data = data
        self.pos = offset
        self.bit = 0
        self.end = len(data)

    def read1(self):
        if self.pos >= self.end:
            raise EOFError("bitstream exhausted")
        ret = (self.data[self.pos] >> self.bit) & 1
        if self.bit >= 7:
            self.pos += 1
            self.bit = 0
        else:
            self.bit += 1
        return ret

    def read8(self):
        if self.bit == 0:
            if self.pos >= self.end:
                raise EOFError("bitstream exhausted")
            v = self.data[self.pos]
            self.pos += 1
            return v
        else:
            if self.pos + 1 >= self.end:
                raise EOFError("bitstream exhausted")
            v = self.data[self.pos] >> self.bit
            self.pos += 1
            v |= (self.data[self.pos] << (8 - self.bit)) & 0xFF
            return v


HUFF8_BRANCH = 0x8000
HUFF8_LEAF_MASK = 0x7FFF

def huff8_build(bs):
    """Reads one Smacker-format Huffman tree (the "big tree" variant used
    for DPCM delta values) directly off the bitstream, per libsmacker's
    algorithm. In: bs (a BitReader positioned at the tree's first bit).
    Out: tree - a flat list where each branch node is `HUFF8_BRANCH |
    right_child_index` (left child is always index+1) and each leaf is a
    literal byte value 0-255; consumes exactly the tree's own bits from bs
    (leaves bs positioned right after it, ready for the encoded data)."""
    tree = []

    def build_rec():
        bit = bs.read1()
        if bit:
            idx = len(tree)
            tree.append(0)  # placeholder
            build_rec()  # left
            tree[idx] = HUFF8_BRANCH | len(tree)  # jump to right subtree start
            build_rec()  # right
        else:
            value = bs.read8()
            tree.append(value)

    has_tree = bs.read1()
    if has_tree:
        build_rec()
    else:
        tree.append(0)
    end_bit = bs.read1()
    if end_bit:
        raise ValueError("huff8_build: malformed tree (expected trailing 0 bit)")
    return tree

def huff8_lookup(tree, bs):
    """Decodes ONE symbol by walking tree bit-by-bit from the bitstream.
    In: tree (from huff8_build), bs (positioned at the start of one
    encoded symbol). Out: int 0-255 - the decoded literal byte (a DPCM
    delta value); consumes exactly that symbol's bits from bs."""
    index = 0
    while tree[index] & HUFF8_BRANCH:
        bit = bs.read1()
        if bit:
            index = tree[index] & HUFF8_LEAF_MASK
        else:
            index += 1
    return tree[index]


def decode_smk_dpcm_chunk(payload, channels, bitdepth16):
    """payload: bytes of one per-frame audio sub-chunk, WITHOUT the leading
    4-byte total-size header (that belongs to the outer frame parser).
    Returns raw PCM bytes (unsigned 8-bit, or signed 16-bit LE)."""
    if len(payload) < 4:
        raise ValueError("audio chunk too short")
    unpacked_size = struct.unpack_from("<I", payload, 0)[0]
    bs = BitReader(payload, 4)

    bit = bs.read1()
    if not bit:
        raise ValueError("expected leading 1 bit in audio bitstream")
    stereo_bit = bs.read1()
    stereo = (stereo_bit == 1)
    depth_bit = bs.read1()
    is16 = (depth_bit == 1)
    if is16 != bitdepth16:
        pass  # header mismatch warning suppressed - proceed with stream's own flags
    if stereo != channels:
        pass

    tree0 = huff8_build(bs)
    tree1 = huff8_build(bs) if is16 else None
    if stereo:
        tree2 = huff8_build(bs)
        tree3 = huff8_build(bs) if is16 else None
    else:
        tree2 = tree3 = None

    nchan = 2 if stereo else 1

    if is16:
        samples = bytearray(unpacked_size)  # will hold int16 samples, 2 bytes each

        def get16(i):
            return struct.unpack_from("<h", samples, i * 2)[0]
        def set16(i, v):
            v &= 0xFFFF
            struct.pack_into("<H", samples, i * 2, v)

        if stereo:
            hi = bs.read8(); lo = bs.read8()
            set16(1, (lo | (hi << 8)))
        hi = bs.read8(); lo = bs.read8()
        set16(0, (lo | (hi << 8)))

        j = 2 if stereo else 1
        k = 4 if stereo else 2
        while k < unpacked_size:
            d_lo = huff8_lookup(tree0, bs)
            d_hi = huff8_lookup(tree1, bs)
            delta = d_lo | (d_hi << 8)
            if delta >= 0x8000:
                delta -= 0x10000
            prev = get16(j - nchan)
            set16(j, delta + prev)
            j += 1
            k += 2
            if stereo:
                d_lo = huff8_lookup(tree2, bs)
                d_hi = huff8_lookup(tree3, bs)
                delta = d_lo | (d_hi << 8)
                if delta >= 0x8000:
                    delta -= 0x10000
                prev = get16(j - 2)
                set16(j, delta + prev)
                j += 1
                k += 2
        return bytes(samples)
    else:
        samples = bytearray(unpacked_size)

        if stereo:
            samples[1] = bs.read8() & 0xFF
        samples[0] = bs.read8() & 0xFF

        j = 2 if stereo else 1
        k = 2 if stereo else 1
        while k < unpacked_size:
            d = huff8_lookup(tree0, bs)
            if d >= 0x80:
                d -= 0x100
            samples[j] = (d + samples[j - nchan]) & 0xFF
            j += 1
            k += 1
            if stereo:
                d = huff8_lookup(tree2, bs)
                if d >= 0x80:
                    d -= 0x100
                samples[j] = (d + samples[j - 2]) & 0xFF
                j += 1
                k += 1
        return bytes(samples)


def extract_smk_audio(path, track=0, out_wav=None):
    """Top-level entry point: parses an .smk file's container (signature,
    frame table, per-track audio format flags) and decodes every frame's
    audio sub-chunk for one track via decode_smk_dpcm_chunk, concatenating
    the PCM output. In: path (.smk file), track (which of up to 4 audio
    tracks to decode - HoMM3 files only ever use track 0), out_wav
    (optional path - if given, also writes a playable .wav via the stdlib
    `wave` module). Out: raw PCM bytes for the whole file (concatenation
    of every frame's decoded chunk, in order) - decode this project's own
    way, or just pass out_wav to get a normal .wav file instead."""
    with open(path, "rb") as f:
        data = f.read()

    p = 0
    sig = data[p:p+3]; p += 3
    if sig != b"SMK":
        raise ValueError(f"not an SMK file (sig={sig!r})")
    p += 1  # version

    _width, _height, nframes, _frate, flags = struct.unpack_from("<IIIii", data, p)
    p += 20
    ring_frame = 1 if (flags & 0x01) else 0

    p += 28  # max_buffer (7 uint32)
    tree_size = struct.unpack_from("<I", data, p)[0]; p += 4
    p += 16  # video_tree_sizes (4 uint32)

    audio_tracks = []
    for _t in range(7):
        rate_field = struct.unpack_from("<I", data, p)[0]; p += 4
        exists = bool(rate_field & 0x40000000)
        compressed = bool(rate_field & 0x80000000)
        bitdepth16 = bool(rate_field & 0x20000000)
        stereo = bool(rate_field & 0x10000000)
        bink = bool(rate_field & 0x0c000000)
        rate = rate_field & 0x00FFFFFF
        audio_tracks.append({"exists": exists, "compressed": compressed,
                              "bitdepth16": bitdepth16, "stereo": stereo,
                              "bink": bink, "rate": rate})

    p += 4  # dummy (reserved uint32)

    total_frames = nframes + ring_frame
    chunk_sizes = []
    keyframes = []
    for _i in range(total_frames):
        v = struct.unpack_from("<I", data, p)[0]; p += 4
        keyframes.append(bool(v & 1))
        chunk_sizes.append(v & 0xFFFFFFFC)

    frame_types = list(data[p:p+total_frames]); p += total_frames

    # skip the video hufftree chunk entirely - we don't decode video here
    p += tree_size

    tr = audio_tracks[track]
    if not tr["exists"]:
        raise ValueError(f"track {track} does not exist in this file")
    if tr["bink"]:
        raise ValueError("Bink-compressed audio track, not supported by this decoder")

    pcm_chunks = []
    for i in range(total_frames):
        chunk = data[p:p+chunk_sizes[i]]
        p += chunk_sizes[i]
        cp = 0
        ft = frame_types[i]

        if ft & 0x01:
            # palette record: first byte * 4 = total bytes of this record
            psize = 4 * chunk[cp]
            cp += psize

        for t in range(7):
            if ft & (0x02 << t):
                blk_size = struct.unpack_from("<I", chunk, cp)[0]
                payload = chunk[cp+4:cp+blk_size]
                if t == track:
                    if tr["compressed"]:
                        pcm = decode_smk_dpcm_chunk(payload, tr["stereo"], tr["bitdepth16"])
                    else:
                        pcm = payload  # raw PCM already
                    pcm_chunks.append(pcm)
                cp += blk_size
        # remainder of chunk (cp .. end) is video data, ignored

    full_pcm = b"".join(pcm_chunks)

    if out_wav:
        nch = 2 if tr["stereo"] else 1
        sampwidth = 2 if tr["bitdepth16"] else 1
        with wave.open(out_wav, "wb") as w:
            w.setnchannels(nch)
            w.setsampwidth(sampwidth)
            w.setframerate(tr["rate"])
            if sampwidth == 1:
                # WAV 8-bit is unsigned - matches our decode already
                w.writeframes(full_pcm)
            else:
                w.writeframes(full_pcm)

    return full_pcm, tr


if __name__ == "__main__":
    import sys
    path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else path + ".wav"
    pcm, tr = extract_smk_audio(path, track=0, out_wav=out)
    print(f"track info: {tr}")
    print(f"decoded {len(pcm)} bytes of PCM -> {out}")
