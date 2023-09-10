import hashlib


class MerkleNode:
    def __init__(self, data):
        self.data = data
        self.left = None
        self.right = None
        self.value = None


def build_merkle_tree(q):
    # if len(transactions) == 0:
    #     return None
    #
    # if len(transactions) == 1:
    #     return MerkleNode(transactions[0])
    height = 0
    nodes = [MerkleNode('_') for _ in range(q)]
    for n in nodes:
        g = n.data
        # print(g)
        n.value = g
        n.data = hashlib.sha256(g.encode('utf-8')).hexdigest()
        # print(n.data)
    # print(type(nodes[0]))

    while len(nodes) > 1:
        parent_level = []
        for i in range(0, len(nodes) - 1, 2):
            data = nodes[i].data + nodes[i + 1].data
            # print(data)
            hash_value = hashlib.sha256(data.encode()).hexdigest()

            parent_node = MerkleNode(hash_value)
            parent_node.left = nodes[i]
            parent_node.right = nodes[i + 1]
            parent_level.append(parent_node)

        if len(nodes) % 2 == 1:
            parent_level.append(nodes[-1])

        nodes = parent_level
        height += 1
    # print("ID注册索引树的高度：", height + 1)
    return nodes[0]


def calculate_merkle_root(q):
    merkle_tree = build_merkle_tree(q)
    return merkle_tree if merkle_tree else None


# global_var = 0


def find_leaf(data_id, node, q):
    # global global_var
    loc = data_id % q
    # if loc % 2 == 0:
    #     global_var = 0
    # else:
    #     global_var = 1
    binary_str = f'{loc:13b}'  # 改
    v = []
    for bit in binary_str:
        v.append(bit)
    return _find_leaf(v, node)


def _find_leaf(array, node):
    vo = []
    vo.append('[')
    n = node
    if n.right is not None and n.left is not None:
        w = array.pop(0)

        if w == '1':
            if n.left.value is not None and n.right.value is not None:
                vo.append(n.left.data)
                vo.append('[')
                vo.append(n.right.value)
                vo.append(']')
            else:
                vo.append(n.left.data)
                vo.extend(_find_leaf(array, n.right))  # 递归调用时传入修改后的数组
        else:
            if n.left.value is not None and n.right.value is not None:

                vo.append('[')
                vo.append(n.left.value)
                vo.append(']')
                vo.append(n.right.data)
            else:

                vo.extend(_find_leaf(array, n.left))  # 递归调用时传入修改后的数组
                vo.append(n.right.data)

        vo.append(']')
    return vo


def verify_root(vo):
    global global_var
    str1 = ''

    # e = vo[0]
    # if e is not None:
    while vo:
        e = str(vo.pop(0))
        if len(e) == 64:
            str1 += e
        elif e == '[':
            # if global_var == 0:
            hash_value = verify_root(vo)
            str1 += hash_value
            # else:
            #     hash_value = verify_root(vo)
            #     str1 += hash_value
        elif e == ']':
            return hashlib.sha256(str1.encode('utf-8')).hexdigest()
        else:
            # r = hashlib.sha256(e.encode('utf-8')).hexdigest()
            str1 += e

    return str1


def find_leaf_update(val, node):
    n = node
    for bit in val:
        if bit == '1':
            n = n.right
        else:
            n = n.left
    return n


def find_l(idn, node, q):
    loc = idn % q
    binary_str = f'{loc:13b}'  # 需要修改
    # print(binary_str)
    v = []
    for bit in binary_str:
        v.append(bit)
    n = find_leaf_update(v, node)
    return n


def update_data(data_id, q, root_node, data):
    loc = data_id % q
    binary_str = f'{loc:13b}'
    # print(binary_str)
    v = []
    for bit in binary_str:
        v.append(bit)
    n = find_leaf_update(v, root_node)
    n.value = data
    n.data = hashlib.sha256(str(data).encode('utf-8')).hexdigest()
    update_relate(v, root_node)
    pr = update_proof(v, root_node)

    # print(pr)
    t, hl = re_comp_root_hash(pr)
    return t, hl


def update_relate(val, node):
    l = len(val)
    # print(l)
    while l:
        n = node
        yy = val[:l - 1]
        for bit in yy:
            if n is None:
                # 如果 n 为 None，则无法访问 n.left 或 n.right，直接退出循环
                return
            if bit == '1':
                n = n.right
            else:
                n = n.left

        if n is None:
            # 如果在更新 n 后 n 变为 None，则无法访问 n.left 或 n.right，直接退出循环
            return

        n_l = n.left
        n_r = n.right
        data_1 = n_l.data + n_r.data
        n.data = hashlib.sha256(data_1.encode()).hexdigest()
        l = l - 1
        data_2 = node.left.data + node.right.data
        # print(node.left.data,node.right.data)
        node.data = hashlib.sha256(data_2.encode()).hexdigest()
        # print(node.data)
        # print(yy)


def update_proof(array, node):
    pr = []
    pr.append('[')
    n = node
    if n.right is not None and n.left is not None:
        w = array.pop(0)

        if w == '1':
            if n.left.value is not None and n.right.value is not None:
                pr.append(n.left.data)
                pr.append('[')
                pr.append(n.right.value)
                pr.append(']')
            else:
                pr.append(n.left.data)
                pr.extend(_find_leaf(array, n.right))  # 递归调用时传入修改后的数组
        else:
            if n.left.value is not None and n.right.value is not None:

                pr.append('[')
                pr.append(n.left.value)
                pr.append(']')
                pr.append(n.right.data)
            else:
                pr.append(n.right.data)
                pr.extend(_find_leaf(array, n.left))  # 递归调用时传入修改后的数组

        pr.append(']')
    return pr


def re_comp_root_hash(pr, hash_list=None):
    if hash_list is None:
        hash_list = []

    str1 = ''

    while pr:
        e = pr.pop(0)
        if len(str(e)) == 64:
            str1 += e
        elif e == '[':
            hash_value = re_comp_root_hash(pr, hash_list)  # 递归调用，将哈希值列表传递给下一层递归
            str1 += hash_value
        elif e == ']':
            hash_value = hashlib.sha256(str1.encode('utf-8')).hexdigest()
            hash_list.append(hash_value)  # 将哈希值添加到列表中
            return hash_value
        else:
            str1 += str(e)

    return str1, hash_list  # 返回哈希值列表

# 示例交易列表
# transactions = ["txbb1", "tx2", "tx3", "tx4", "tx5"]

# 计算默克尔根
# merkle_root = calculate_merkle_root(180)
# m = merkle_root.data
# i = 0
# for i in range(180):
#     update_data(i,180,merkle_root,str(i))
# print(type(merkle_root))
# print("Merkle Root:", m)
# n = merkle_root.left.left.right
# print(n.data,n.data)
# n = "0101"
# for bit in n:
#     if bit == '1':
#         print(1)
#     else:
#         print(0)
# leaf_node = find_leaf(3, merkle_root, 8)
# print(leaf_node)
# a = verify_root(leaf_node)
# print(a)
# print(m == a)
# p = find_leaf_update(n, merkle_root)
# print(p.data)
# update_data(0, 180, merkle_root, '18')
# update_data(1, 180, merkle_root, '16')
# update_data(2, 16, merkle_root, '82')
# update_data(3, 16, merkle_root, '52')
# update_data(4, 16, merkle_root, '89')
# update_data(5, 16, merkle_root, '24')
# update_data(6, 16, merkle_root, '72')
# update_data(7, 16, merkle_root, '22')
# update_data(8, 16, merkle_root, '74')
# update_data(9, 16, merkle_root, '78')
# update_data(10, 16, merkle_root, '81')
# update_data(11, 16, merkle_root, '73')
# update_data(12, 16, merkle_root, '93')
# update_data(13, 16, merkle_root, '56')
# update_data(14, 16, merkle_root, '98')
# f, hl = update_data(15, 16, merkle_root, '16')
# print(f)
# print(hl)
# print(merkle_root.left.left.right.left.value)

# v = []
# for bit in "01011100":
#     v.append(bit)
# print(v)
# print(v.pop(0))
# print(v)
