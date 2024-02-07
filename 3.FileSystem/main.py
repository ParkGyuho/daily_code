#!/usr/bin/env python

from byte_buffer2 import *


class Superblock:
    def __init__(self, bb):
        bb.offset = 0xb
        self.sector_size = bb.get_uint2_le()  # 1섹터 당 바이트 수
        self.sector_count = bb.get_uint1()  # 1클러스터 당 섹터 수
        self.cluster_size = self.sector_size * self.sector_count  # 1클러스터 당 크기
        bb.offset = 0xe
        self.sector_no = bb.get_uint2_le()  # 예약된 영역의 섹터 수
        bb.offset = 0x30-4
        self.root_cluster_no = bb.get_uint4_le()  # 루트 디렉토리 클러스터 번호
        # FAT영역 시작 주소 = 예약된 영역 섹터 수 * 섹터 크기
        self.fat_area_address = self.sector_no * self.sector_size
        bb.offset = 0x24
        # FAT영역 크기 = FAT 영역의 섹터 수 * 섹터 크기
        self.fat_area_size = bb.get_uint4_le() * self.sector_size
        # Data 영역 시작 주소 = FAT 영역 시작 주소 + FAT 영역 총 크기
        self.data_address = self.fat_area_address + (0x2 * self.fat_area_size)

    def __str__(self):
        return (f"sector size: {hex(self.sector_size)}\n"
                f"sector count: {hex(self.sector_count)}\n"
                f"cluster size: {hex(self.cluster_size)}\n"
                f"sector number: {hex(self.sector_no)}\n"
                f"root cluster no: {hex(self.root_cluster_no)}\n"
                f"fat area address: {hex(self.fat_area_address)}\n"
                f"fat area size: {hex(self.fat_area_size)}\n"
                f"data address: {hex(self.data_address)}")


class FatArea:
    def __init__(self, buffer):
        entry_count = len(buffer) // 4
        bb2 = ByteBuffer2(buffer)
        self.fat = []
        for i in range(entry_count):
            self.fat.append(bb2.get_uint4_le())

    def __str__(self):
        return ' '.join(hex(i) for i in self.fat[:10])

    def get_cluster(self, start_cluster_no):
        self.cluster_list = []
        next = start_cluster_no

        while next != 0xfffffff:
            self.cluster_list.append(next)
            next = self.fat[next]

        return self.cluster_list


class DirectoryEntry:
    def __init__(self, bb):
        bb.offset = 0xb
        self.is_file = False
        attr = bb.get_uint1()

        if attr == 0x20:
            self.is_file = True

        bb.offset = 0x14
        cluster_hi = bb.get_uint2_le()
        bb.offset = 0x1A
        cluster_low = bb.get_uint2_le()

        self.cluster_no = (cluster_hi << 16) | cluster_low


def export_to(Superblock, cluster_list, file, path):
    start_add = Superblock.data_address + \
        (cluster_list[0] - 2) * Superblock.cluster_size
    end_add = Superblock.data_address + \
        (cluster_list[-1] - 2) * Superblock.cluster_size
    # print(hex(start_add), hex(end_add))

    with open(path, 'wb') as f:
        file.seek(start_add)
        b = file.read(end_add-start_add)
        f.write(b)


if __name__ == "__main__":
    buffer = None
    with open('FAT32_simple.mdf', 'rb') as file:
        file.seek(0)
        buffer = file.read(0x200)
        bb = ByteBuffer2(buffer)
        sb = Superblock(bb)
        print(sb)

        file.seek(sb.fat_area_address)
        buffer2 = file.read(sb.fat_area_size)
        fat = FatArea(buffer2)
        print(fat)

        leaf_addr = 0x404040
        file.seek(leaf_addr)
        buffer3 = file.read(0x20)
        bb3 = ByteBuffer2(buffer3)
        leaf = DirectoryEntry(bb3)
        leaf_cluster = fat.get_cluster(leaf.cluster_no)
        export_to(sb, leaf_cluster, file, "leaf.jpg")

        port_addr = 0x404060
        file.seek(port_addr)
        buffer4 = file.read(0x20)
        bb4 = ByteBuffer2(buffer4)
        port = DirectoryEntry(bb4)
        port_cluster = fat.get_cluster(port.cluster_no)
        export_to(sb, port_cluster, file, "port.jpg")
