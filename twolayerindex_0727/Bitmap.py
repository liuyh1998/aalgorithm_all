class Bitmap:
    def __init__(self, size):
        self.size = size
        self.bitmap = 0

    def set_bit(self, position, value):
        if position < 0 or position >= self.size:
            raise IndexError("Invalid position")
        mask = 1 << position
        if value == 1:
            self.bitmap |= mask
        else:
            self.bitmap &= ~mask

    # def get_set_bits(self):
    #     set_bits = []
    #     for i in range(self.size):
    #         mask = 1 << i
    #         if self.bitmap & mask:
    #             set_bits.append(i)
    #     return set_bits
    def get_set_bits(self):
        set_bits = []
        bitmap = self.bitmap
        index = 0

        while bitmap:
            if bitmap & 1:
                set_bits.append(index)
            bitmap >>= 1
            index += 1

        return set_bits

    def show_bitmap(self):
        bitmap_str = bin(self.bitmap)[2:].zfill(self.size)
        return bitmap_str

    def check_bit(self, position):
        if position < 0 or position >= self.size:
            raise IndexError("Invalid position")
        mask = 1 << position
        return (self.bitmap & mask) != 0

# a = Bitmap(8)
# a.set_bit(0,1)
# print(a.show_bitmap())
# print(a.check_bit(0))