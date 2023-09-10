from __future__ import annotations
from math import ceil, floor
import hashlib
import time

class Node:
    uid_counter = 0
    """
    Base node object.

    Attributes:
        order (int): The maximum number of keys each node can hold. (aka branching factor)
    """

    def __init__(self, order):
        self.order = order
        self.parent: Node = None
        self.keys = []
        self.values = []
        self.hash_value = None

        #  This is for Debugging purposes only!
        Node.uid_counter += 1
        self.uid = self.uid_counter

    def split(self) -> Node:  # Split a full Node to two new ones.
        left = Node(self.order)
        right = Node(self.order)
        mid = int(self.order // 2)

        left.parent = right.parent = self

        left.keys = self.keys[:mid]
        left.values = self.values[:mid + 1]

        right.keys = self.keys[mid + 1:]
        right.values = self.values[mid + 1:]

        self.values = [left, right]  # Setup the pointers to child nodes.

        self.keys = [self.keys[mid]]  # Hold the first element from the right subtree.

        # Setup correct parent for each child node.
        for child in left.values:
            if isinstance(child, Node):
                child.parent = left

        for child in right.values:
            if isinstance(child, Node):
                child.parent = right

        return self  # Return the 'top node'

    # def range_query(self, start_key, end_key):
    #     results = []
    #
    #     if self.is_leaf():
    #         for i, key in enumerate(self.keys):
    #             if start_key <= key <= end_key:
    #                 results.extend(self.values[i])
    #             elif key > end_key:
    #                 break
    #     else:
    #         for i, key in enumerate(self.keys):
    #             if start_key <= key:
    #                 results.extend(self.values[i].range_query(start_key, end_key))
    #             elif key > end_key:
    #                 break
    #
    #     return results

    def get_size(self) -> int:
        return len(self.keys)

    def is_empty(self) -> bool:
        return len(self.keys) == 0

    def is_full(self) -> bool:
        return len(self.keys) == self.order - 1

    def is_nearly_underflowed(self) -> bool:  # Used to check on keys, not data!
        return len(self.keys) <= floor(self.order / 2)

    def is_underflowed(self) -> bool:  # Used to check on keys, not data!
        return len(self.keys) <= floor(self.order / 2) - 1

    def is_root(self) -> bool:
        return self.parent is None

    def is_leaf(self) -> bool:
        return isinstance(self, LeafNode)


class LeafNode(Node):

    def __init__(self, order):
        super().__init__(order)

        self.prev_leaf: LeafNode = None
        self.next_leaf: LeafNode = None

    def add(self, key, value):  # TODO: Implement improved version
        if not self.keys:  # Insert key if it doesn't exist
            self.keys.append(key)
            self.values.append([value])
            return

        for i, item in enumerate(self.keys):  # Otherwise, search key and append value.
            if key == item:  # Key found => Append Value
                self.values[i].append(value)  # Remember, this is a list of data. Not nodes!
                break

            elif key < item:  # Key not found && key < item => Add key before item.
                self.keys = self.keys[:i] + [key] + self.keys[i:]
                self.values = self.values[:i] + [[value]] + self.values[i:]
                break

            elif i + 1 == len(self.keys):  # Key not found here. Append it after.
                self.keys.append(key)
                self.values.append([value])
                break

    def split(self) -> Node:  # Split a full leaf node. (Different method used than before!)
        top = Node(self.order)
        right = LeafNode(self.order)
        mid = int(self.order // 2)

        self.parent = right.parent = top

        right.keys = self.keys[mid:]
        right.values = self.values[mid:]
        right.prev_leaf = self
        right.next_leaf = self.next_leaf

        top.keys = [right.keys[0]]
        top.values = [self, right]  # Setup the pointers to child nodes.

        self.keys = self.keys[:mid]
        self.values = self.values[:mid]
        self.next_leaf = right  # Setup pointer to next leaf

        return top  # Return the 'top node'


class BPlusTree(object):
    def __init__(self, order=5):
        self.root: Node = LeafNode(order)  # First node must be leaf (to store data).
        self.order: int = order
        # self.calculate_leaf_hash()

    @staticmethod
    def _find(node: Node, key):
        for i, item in enumerate(node.keys):
            if key < item:
                return node.values[i], i
            elif i + 1 == len(node.keys):
                return node.values[i + 1], i + 1  # return right-most node/pointer.

    @staticmethod
    def _merge_up(parent: Node, child: Node, index):
        parent.values.pop(index)
        pivot = child.keys[0]

        for c in child.values:
            if isinstance(c, Node):
                c.parent = parent

        for i, item in enumerate(parent.keys):
            if pivot < item:
                parent.keys = parent.keys[:i] + [pivot] + parent.keys[i:]
                parent.values = parent.values[:i] + child.values + parent.values[i:]
                break

            elif i + 1 == len(parent.keys):
                parent.keys += [pivot]
                parent.values += child.values
                break

    def insert(self, key, value):
        node = self.root

        while not isinstance(node, LeafNode):  # While we are in internal nodes... search for leafs.
            node, index = self._find(node, key)

        # Node is now guaranteed a LeafNode!
        node.add(key, value)

        while len(node.keys) == node.order:  # 1 over full
            if not node.is_root():
                parent = node.parent
                node = node.split()  # Split & Set node as the 'top' node.
                jnk, index = self._find(parent, node.keys[0])
                self._merge_up(parent, node, index)
                node = parent
            else:
                node = node.split()  # Split & Set node as the 'top' node.
                self.root = node  # Re-assign (first split must change the root!)
        self.calculate_leaf_hash()
        self.calculate_non_leaf_hash()

    def retrieve(self, key):
        node = self.root

        while not isinstance(node, LeafNode):
            node, index = self._find(node, key)

        for i, item in enumerate(node.keys):
            if key == item:
                return node.values[i]

        return None

    def delete(self, key):
        node = self.root

        while not isinstance(node, LeafNode):
            node, parent_index = self._find(node, key)

        if key not in node.keys:
            return False

        index = node.keys.index(key)
        node.values[index].pop()  # Remove the last inserted data.

        if len(node.values[index]) == 0:
            node.values.pop(index)  # Remove the list element.
            node.keys.pop(index)

            while node.is_underflowed() and not node.is_root():
                # Borrow attempt:
                prev_sibling = BPlusTree.get_prev_sibling(node)
                next_sibling = BPlusTree.get_next_sibling(node)
                jnk, parent_index = self._find(node.parent, key)

                if prev_sibling and not prev_sibling.is_nearly_underflowed():
                    self._borrow_left(node, prev_sibling, parent_index)
                elif next_sibling and not next_sibling.is_nearly_underflowed():
                    self._borrow_right(node, next_sibling, parent_index)
                elif prev_sibling and prev_sibling.is_nearly_underflowed():
                    self._merge_on_delete(prev_sibling, node)
                elif next_sibling and next_sibling.is_nearly_underflowed():
                    self._merge_on_delete(node, next_sibling)

                node = node.parent

            if node.is_root() and not isinstance(node, LeafNode) and len(node.values) == 1:
                self.root = node.values[0]
                self.root.parent = None
        self.calculate_leaf_hash()
        self.calculate_non_leaf_hash()

    @staticmethod
    def _borrow_left(node: Node, sibling: Node, parent_index):
        if isinstance(node, LeafNode):  # Leaf Redistribution
            key = sibling.keys.pop(-1)
            data = sibling.values.pop(-1)
            node.keys.insert(0, key)
            node.values.insert(0, data)

            node.parent.keys[parent_index - 1] = key  # Update Parent (-1 is important!)
        else:  # Inner Node Redistribution (Push-Through)
            parent_key = node.parent.keys.pop(-1)
            sibling_key = sibling.keys.pop(-1)
            data: Node = sibling.values.pop(-1)
            data.parent = node

            node.parent.keys.insert(0, sibling_key)
            node.keys.insert(0, parent_key)
            node.values.insert(0, data)

    @staticmethod
    def _borrow_right(node: LeafNode, sibling: LeafNode, parent_index):
        if isinstance(node, LeafNode):  # Leaf Redistribution
            key = sibling.keys.pop(0)
            data = sibling.values.pop(0)
            node.keys.append(key)
            node.values.append(data)
            node.parent.keys[parent_index] = sibling.keys[0]  # Update Parent
        else:  # Inner Node Redistribution (Push-Through)
            parent_key = node.parent.keys.pop(0)
            sibling_key = sibling.keys.pop(0)
            data: Node = sibling.values.pop(0)
            data.parent = node

            node.parent.keys.append(sibling_key)
            node.keys.append(parent_key)
            node.values.append(data)

    @staticmethod
    def _merge_on_delete(l_node: Node, r_node: Node):
        parent = l_node.parent

        jnk, index = BPlusTree._find(parent, l_node.keys[0])  # Reset pointer to child
        parent_key = parent.keys.pop(index)
        parent.values.pop(index)
        parent.values[index] = l_node

        if isinstance(l_node, LeafNode) and isinstance(r_node, LeafNode):
            l_node.next_leaf = r_node.next_leaf  # Change next leaf pointer
        else:
            l_node.keys.append(parent_key)  # TODO Verify dis
            for r_node_child in r_node.values:
                r_node_child.parent = l_node

        l_node.keys += r_node.keys
        l_node.values += r_node.values

    def calculate_leaf_hash(self):
        n = self.get_leftmost_leaf()
        while n is not None:
            s = ''
            for (key, value) in zip(n.keys, n.values):
                for i in value:
                    s += (str(key) + i)
            n.hash_value = hashlib.sha256(s.encode('utf-8')).hexdigest()
            # print('叶节点哈希值：' + n.hash_value)
            n = n.next_leaf

    def calculate_non_leaf_hash(self):
        queue = [self.root]
        node_list = []
        while queue:
            n = queue.pop(0)
            if n.is_leaf():
                return
            for i in n.values:
                if not i.is_leaf():
                    queue.append(i)
            node_list.append(n)
        print(node_list)

        while node_list:
            ss = ''
            bb = node_list.pop()
            for o in bb.values:
                ss += o.hash_value
            qq = hashlib.sha256(ss.encode('utf-8')).hexdigest()
            bb.hash_value = qq
            print(qq)

    def range_query(self, start_key, end_key):
        node = self.root

        while not isinstance(node, LeafNode):
            node, index = self._find(node, start_key)

        results = []
        while node:
            for i, key in enumerate(node.keys):
                if start_key <= key <= end_key:
                    results.extend(node.values[i])
                elif key > end_key:
                    return results

            node = node.next_leaf

        return results

    def construct_vo(self, node, start_key, end_key):

        vo = []
        current_node = node
        # vo.append('[')
        if current_node.is_leaf():
            for (key, value) in zip(current_node.keys, current_node.values):
                if start_key <= key <= end_key:
                    vo.append('[')

                    for (i, j) in zip(current_node.keys, current_node.values):
                        # vo.append('[')
                        vo.append(str(i))
                        vo.extend(j)
                        # vo.append(']')
                    vo.append(']')
                    break
                elif key > end_key:
                    vo.append(current_node.hash_value)
                    break
                elif max(current_node.keys) < start_key:
                    vo.append(current_node.hash_value)
                    break
                # else:
                #     vo.append(current_node.hash_value)
                #     break
        else:
            # for key in current_node.keys:

            if start_key <= max(current_node.keys):
                vo.append('[')
                for child_node in current_node.values:
                    # vo.append('[')
                    vo.extend(self.construct_vo(child_node, start_key, end_key))
                    # 将当前节点标记为已处理
                    # vo.append(']')
                vo.append(']')
            elif end_key < min(current_node.keys):
                vo.append(current_node.hash_value)
            elif start_key > max(current_node.keys):
                vo.append(current_node.hash_value)

                    # break
        # vo.append(']')
        return vo

    def re_root(self, vo):
        str1 = ''
        # e = vo[0]
        # if e is not None:
        while vo:
            e = vo.pop(0)
            if len(e) == 64:
                str1 += e
            elif e == '[':
                hash_value = self.re_root(vo)
                str1 += hash_value
            elif e == ']':
                return hashlib.sha256(str1.encode('utf-8')).hexdigest()
            else:
                # r = hashlib.sha256(e.encode('utf-8')).hexdigest()
                str1 += e

        return str1

    @staticmethod
    def get_prev_sibling(node: Node) -> Node:
        if node.is_root() or not node.keys:
            return None
        jnk, index = BPlusTree._find(node.parent, node.keys[0])
        return node.parent.values[index - 1] if index - 1 >= 0 else None

    @staticmethod
    def get_next_sibling(node: Node) -> Node:
        if node.is_root() or not node.keys:
            return None
        jnk, index = BPlusTree._find(node.parent, node.keys[0])

        return node.parent.values[index + 1] if index + 1 < len(node.parent.values) else None

    def show_bfs(self):
        if self.root.is_empty():
            print('The B+ Tree is empty!')
            return
        queue = [self.root, 0]  # Node, Height... Scrappy but it works

        while len(queue) > 0:
            node = queue.pop(0)
            height = queue.pop(0)

            if not isinstance(node, LeafNode):
                queue += self.intersperse(node.values, height + 1)
            print(height, '|'.join(map(str, node.keys)), '\t', node.uid, '\t parent -> ',
                  node.parent.uid if node.parent else None)

    def get_leftmost_leaf(self):
        if not self.root:
            return None

        node = self.root
        while not isinstance(node, LeafNode):
            node = node.values[0]

        return node

    def get_rightmost_leaf(self):
        if not self.root:
            return None

        node = self.root
        while not isinstance(node, LeafNode):
            node = node.values[-1]

    def show_all_data(self):
        node = self.get_leftmost_leaf()
        if not node:
            return None

        while node:
            for node_data in node.values:
                print('[{}]'.format(', '.join(map(str, node_data))), end=' -> ')

            node = node.next_leaf
        print('Last node')

    def show_all_data_reverse(self):
        node = self.get_rightmost_leaf()
        if not node:
            return None

        while node:
            for node_data in reversed(node.values):
                print('[{}]'.format(', '.join(map(str, node_data))), end=' <- ')

            node = node.prev_leaf
        print()

    @staticmethod
    def intersperse(lst, item):
        result = [item] * (len(lst) * 2)
        result[0::2] = lst
        return result


if __name__ == '__main__':
    print('Initializing B+ tree...')
    bplustree = BPlusTree(order=4)
    s_t = time.perf_counter()
    bplustree.insert(13, 'November')

    bplustree.insert(0, '_')
    bplustree.insert(7, 'Hotel')
    bplustree.insert(8, 'India')
    bplustree.insert(5, 'Echo')
    bplustree.insert(6, 'Golf')
    bplustree.insert(4, 'Delta')
    bplustree.insert(1, 'Alpha')
    bplustree.insert(2, 'Bravo')
    bplustree.insert(3, 'Charlie')
    bplustree.insert(9, 'Juliet')

    bplustree.insert(81, 'Bravo2')
    bplustree.insert(10, 'Kilo')
    bplustree.insert(11, 'Lima')
    bplustree.insert(12, 'Mike')
    bplustree.insert(17, 'Romeo')
    bplustree.insert(14, 'Oscar')
    bplustree.insert(15, 'Papa')
    bplustree.insert(16, 'Quebec')
    bplustree.insert(57, 'gttg')
    bplustree.insert(22, 'Rtg')
    bplustree.insert(88, 'Oscar')
    bplustree.insert(31, 'Papa')
    bplustree.insert(37, 'Quebec')
    bplustree.insert(39, 'Oscar')
    bplustree.insert(40, 'Papa')
    bplustree.insert(46, 'Quebec')
    bplustree.insert(59, 'Mike')
    bplustree.insert(55, 'Romeo')
    bplustree.insert(333, 'Oscar')
    bplustree.insert(132, 'Papa')
    bplustree.insert(537, 'Quebec')
    bplustree.insert(5555, 'Mike')
    bplustree.insert(666, 'Romeo')
    bplustree.insert(773, 'Oscar')
    bplustree.insert(166, 'Papa')
    bplustree.insert(565, 'Quebec')

    # bplustree.delete(81)
    # bplustree.delete(10)
    # bplustree.delete(11)
    # bplustree.delete(12)
    # bplustree.delete(17)
    # bplustree.delete(14)
    # bplustree.delete(15)
    # bplustree.delete(16)
    # bplustree.delete(57)
    # bplustree.delete(22)
    # bplustree.delete(88)
    # bplustree.delete(31)
    # bplustree.delete(37)
    # bplustree.delete(39)
    # bplustree.delete(40)
    # bplustree.delete(46)
    # bplustree.delete(59)
    # bplustree.delete(55)
    # bplustree.delete(333)
    # bplustree.delete(132)
    # bplustree.delete(537)


    e_t = time.perf_counter()
    construct_time = e_t - s_t
    print(f'构建时间为 {construct_time} ms')
    bplustree.show_bfs()
    bplustree.show_all_data()
    a= bplustree.range_query(1, 10)
    print('范围查询结果：' + str(a))
    # print('vo：' + str(vo))
    # bplustree.calculate_leaf_hash()
    b = bplustree.get_leftmost_leaf().next_leaf
    print(b.hash_value)
    print(str(b.values[1][0]))
    print(b.keys)
    print(b.values)
    # print(bplustree.root.values[0].values[1].values)

    # bplustree.delete(6)
    # bplustree.delete(2)
    # bplustree.delete(2)
    # bplustree.delete(1)
    # bplustree.delete(4)
    # bplustree.delete(8)
    # bplustree.delete(10)
    # bplustree.delete(2)
    # bplustree.delete(3)
    # bplustree.delete(0)
    # bplustree.delete(14)
    # bplustree.delete(11)
    # bplustree.delete(9)
    # bplustree.delete(7)
    # bplustree.delete(12)
    # bplustree.delete(5)
    # bplustree.delete(13)
    # bplustree.delete(15)
    # bplustree.delete(17)
    # bplustree.delete(16)
    #
    # bplustree.show_bfs()
    # bplustree.show_all_data()
    c = bplustree.root
    print(c)
    print(c.keys)
    d = bplustree.construct_vo(c, 8, 70)
    print(d)
    f = bplustree.re_root(d)
    print(f)
    if f == c.hash_value:
        print('验证成功')
    else:
        print('验证失败')
    # queue = [c]
    # node = []
    # while queue:
    #     n = queue.pop(0)
    #     for i in n.values:
    #         if not i.is_leaf():
    #             queue.append(i)
    #     node.append(n)
    # print(node)
    # ss = ''
    # while node:
    #     bb = node.pop()
    #     for o in bb.values:
    #         ss += o.hash_value
    #     qq = hashlib.sha256(ss.encode('utf-8')).hexdigest()
    #     print(qq)
    # bplustree.calculate_non_leaf_hash()
    print(c.hash_value)