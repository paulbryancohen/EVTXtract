#!/bin/python
#    This file is part of recover-evtx.
#
#   Copyright 2013 Willi Ballenthin <william.ballenthin@mandiant.com>
#                    while at Mandiant <http://www.mandiant.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#   Version v0.1
import mmap
import contextlib
import struct

from Evtx.Evtx import ChunkHeader


def offset_seems_like_chunk_header(buf, offset):
    """
    Return True if the offset appears to be an EVTX Chunk header.

    @type buf: bytestring
    @type offset: int
    @rtype boolean
    """
    if struct.unpack_from(buf, "<8s", offset) != "ElfChnk":
        return False
    if not (0x80 <= struct.unpack_from(buf, "<I", offset + 0x28) <= 0x200):
        return False
    return True


class CHUNK_HIT_TYPE:
    """
    Enumeration of types of chunk hits.
    """
    CHUNK_VALID = 0
    CHUNK_BAD_HEADER = 1
    CHUNK_BAD_DATA = 2


def find_evtx_chunks(buf):
    """
    Generates tuples (CHUNK_HIT_TYPE, offset) from the given buffer.

    @type buf: bytestring
    @rtype: generator of (int, int)
    """
    index = buf.find("ElfChnk")
    while index != -1:
        if not offset_seems_like_chunk_header(buf, index):
            index = buf.find("ElfChnk", index + 1)
            continue
        chunk = ChunkHeader(buf, index)

        if chunk.calculate_header_checksum() != chunk.header_checksum():
            yield (CHUNK_HIT_TYPE.CHUNK_BAD_HEADER, index)
        if chunk.calculate_data_checksum() != chunk.data_checksum():
            yield (CHUNK_HIT_TYPE.CHUNK_BAD_DATA, index)
        else:
            yield (CHUNK_HIT_TYPE.CHUNK_VALID, index)
        index = buf.find("ElfChnk", index + 1)
        continue


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Find offsets of EVTX chunk headers.")
    parser.add_argument("evtx", type=str,
                        help="Path to the Windows EVTX file")
    args = parser.parse_args()

    with open(args.evtx, "rb") as f:
        with contextlib.closing(mmap.mmap(f.fileno(), 0,
                                          access=mmap.ACCESS_READ)) as buf:
            for hit_type, offset in find_evtx_chunks(buf):
                if hit_type == CHUNK_HIT_TYPE.CHUNK_BAD_HEADER:
                    print("%s\t%s" % ("CHUNK_BAD_HEADER", hex(offset)))
                elif hit_type == CHUNK_HIT_TYPE.CHUNK_BAD_DATA:
                    print("%s\t%s" % ("CHUNK_BAD_DATA", hex(offset)))
                elif hit_type == CHUNK_HIT_TYPE.CHUNK_VALID:
                    print("%s\t%s" % ("CHUNK_VALID", hex(offset)))
                else:
                    raise "Unknown CHUNK_HIT_TYPE: %d" % hit_type

if __name__ == "__main__":
    main()