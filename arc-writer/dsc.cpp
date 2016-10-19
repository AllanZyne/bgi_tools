
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <set>
#include <queue>
#include <algorithm>
#include <map>
#include <forward_list>
#include <list>
#include <memory>
#include <utility>

#include "optional.hpp"


using namespace std;
using namespace std::experimental;



class DSC_Encript {
    struct DSC_Head {
        char magic[16];  // 'DSC FORMAT 1.00\0'
        unsigned key;
        unsigned size;
        unsigned decCount;
        int reserved;
    } head;

    struct LeafNode {
        int depth;
        int code;
    };

    class TreeNode {
        static int NodeIndex;

        TreeNode* left;
        TreeNode* right;
        int code;
        int index;

    public:
        TreeNode(int code)
            : code(code)
            , index(TreeNode::NodeIndex++)
        {
        }

        TreeNode(TreeNode* left, TreeNode* right)
            : code(-1)
            , left(left)
            , right(right)
            , index(TreeNode::NodeIndex++)
        {
        }

        bool operator<(const TreeNode& node)
        {
            return index < node.index;
        }
    };

    struct CompressPair {
        int code;
        optional<int> offset;
    };

    //typedef pair<int, int> FreqPair;

    struct FreqPair
    {
        int freq;
        TreeNode* node;
    };

    ifstream fin;
    TreeNode tree[1024];

    list<char*> hashTable[0x10000];

#define MATCH_MAX 0xff
#define WINDOW_BIT 12
#define WINDOW_SIZE (1 << 12)

    //char window[WINDOW_SIZE*2];
    char *window;
    char *pCur0, *pEnd0, *pCur;
    //char *pCur1, *pEnd1;

public:
    DSC_Encript()
    {
    }


    int match(char* src, char* dst, char* dst_end)
    {
        char* _src = src;
        while (dst < dst_end && *src == *dst) {
            src++;
            dst++;
        }
        return src - _src;
    }

    bool longestMatch(int& maxSize, int& maxPos)
    {
        char *_pCur = pCur + 1, *_pEnd = _pCur + MATCH_MAX;
        if (_pEnd > pEnd0)
            _pEnd = pEnd0;

        const list<char*>& mPos = hashTable[*reinterpret_cast<unsigned short*>(pCur - 1)];
        if (mPos.empty())
            return false;
        for (char* pPos : mPos) {
            int size = match(pPos, _pCur, _pEnd);
            if (size > maxSize) {
                maxSize = size;
                maxPos = pCur - pPos - 1;
                if (maxSize == MATCH_MAX)
                    return true;
            }
        }
        return true;
    }

    void putHTable(char* pCur) {
        //cout << hex << "putHTable 0x" << *reinterpret_cast<short*>(pCur0 - 2) << endl;
        hashTable[*reinterpret_cast<unsigned short*>(pCur-2)].push_front(pCur);
    }

    void deleteHTable(char* pCur) {
        hashTable[*reinterpret_cast<unsigned short*>(pCur)].pop_back();
    }

    void compress(vector<CompressPair>& out) {
        //ofstream log("log2.txt", ios_base::out);
        //cout << hex << int((unsigned char)*pCur) << endl;
        //log << hex << int((unsigned char)*pCur) << endl;
        out.push_back({ *pCur, nullopt });
        if (pCur + 1 == pEnd0) {
            return;
        }
        pCur += 2;

        while (pCur < pEnd0 ) {
            static int size, pos;
            size = pos = -1;
            longestMatch(size, pos);
            if (size < 0) {
                //cout << hex << int((unsigned char)*(pCur - 1)) << endl;
                //log << hex << int((unsigned char)*(pCur-1)) << endl;
                out.push_back({ *(pCur-1), nullopt });
                putHTable(pCur);
                pCur++;
            } else {
                //cout << hex << (size | 0x100) << ", " << pos << endl;
                //log << hex << (size | 0x100) << ", " << pos << endl;
                out.push_back({ size | 0x100, pos });
                size += 2;
                while (size--) {
                    putHTable(pCur);
                    pCur++;
                }
            }

            int delta = pCur - pCur0 - 1 - WINDOW_SIZE;
            if (delta > 0)
                while (delta--) {
                    deleteHTable(pCur0);
                    pCur0++;
                }
        }
    }

    bool load(const string& fileName)
    {
        fin = ifstream(fileName, ios::binary);
        if (!fin.is_open())
            return false;
        //while (fin.peek() != EOF) {
            fin.seekg(0, ios_base::end);
            unsigned fileSize = static_cast<unsigned>(fin.tellg());
            fin.seekg(0, ios_base::beg);
            if (! fileSize)
                return true;
            window = new char[fileSize];
            fin.read(window, fileSize);
            pCur0 = pCur = window;
            pEnd0 = window + fin.gcount();

        //}
        return true;
    }

    //bool freqpair_compare(const FreqPair& p1, const FreqPair& p2)
    //{
    //    if (p1.freq != p2.freq)
    //        return p1.freq < p2.freq;
    //    else
    //        return p1.code < p2.code;
    //}

    void huffTree(vector<int>& freqs)
    {
        auto freqpair_compare = [](const FreqPair& p1, const FreqPair& p2) -> bool {
            if (p1.freq != p2.freq)
                return p1.freq < p2.freq;
            else
                return p1.node < p2.node;
        };

        priority_queue<FreqPair, vector<FreqPair>, decltype(freqpair_compare)>
        freqs_queue(freqpair_compare);

        for (int i = 0; i < 0x200; i++) {
            if (freqs[i] > 0)
                freqs_queue.emplace(freqs[i], new TreeNode(i));
        }

        while (freqs_queue.size() > 1) {
            const FreqPair& l = freqs_queue.top();
            freqs_queue.pop();
            const FreqPair& r = freqs_queue.top();
            freqs_queue.pop();
            freqs_queue.emplace(l.freq + r.freq, new TreeNode(l.node, r.node));
        }
        TreeNode* root = freqs_queue.top().node;
        
    }

    bool save(const string& fileName)
    {
        //auto cpair_comp = [](const CompressPair& p1, const CompressPair& p2) {
        //    if (p1.code != p2.code)
        //        return p1.code < p2.code;
        //    else
        //        return p1.offset < p2.offset;
        //};

        vector<CompressPair> out;
        compress(out);

        vector<int> freqs(0x200, 0);
        for (auto& p : out) {
            freqs[p.code]++;
        }

        //make_heap(freqs.begin(), freqs.end(), []() {

        //});

        return true;
    }
};


class DSC_Decript {
    struct DSC_Head {
        char magic[16];  // 'DSC FORMAT 1.00\0'
        unsigned key;
        unsigned size;
        unsigned decCount;
        int reserved;
    } head;

    struct LeafNode {
        int depth;
        int code;
    };

    struct TreeNode {
        int left;
        int right;
        optional<int> code;
    };

    ifstream fin;
    TreeNode tree[1024];

public:
    DSC_Decript()
    {
    }

    char keyGen()
    {
        static unsigned key = head.key;
        register unsigned a = (key & 0xffff) * 20021;
        register unsigned b = (key >> 16) * 20021;
        register unsigned c = (key * 346 + b) + (a >> 16);
        key = ((c & 0xffff) << 16) + (a & 0xffff) + 1;
        return c & 0xff;
    }

    void huffmanTree(vector<LeafNode>& leafNodes)
    {
        int treeNodeIndex = 1;
        int nodeIndex[512 * 2] = { 0 };
        int *nodeIndex0 = nodeIndex,
            *nodeIndex1 = &nodeIndex[512];
        int treeDepth = 0;
        int depthNodeCount = 1;

        for (unsigned n = 0; n < leafNodes.size();) {
            swap(nodeIndex0, nodeIndex1);

            int leafNodeCount = 0;
            while (n < leafNodes.size()) {
                LeafNode& leafNode = leafNodes[n];
                if (leafNode.depth == treeDepth) {
                    TreeNode& node = tree[nodeIndex0[leafNodeCount]];
                    node.code = leafNode.code;
                    n++;
                    leafNodeCount++;
                } else
                    break;
            }
            int nodeCount = depthNodeCount - leafNodeCount;
            for (int i = 0; i < nodeCount; i++) {
                TreeNode& node = tree[nodeIndex0[leafNodeCount + i]];
                nodeIndex1[i * 2] = node.left = treeNodeIndex++;
                nodeIndex1[i * 2 + 1] = node.right = treeNodeIndex++;
            }
            depthNodeCount = nodeCount * 2;
            treeDepth++;
        }
    }

    void walkTree()
    {
        map<string, int> codes;

        function<void(int, string)> _walk = [this, &_walk, &codes](int n, const string& prefix) {
            TreeNode& node = tree[n];
            if (!node.code) {
                _walk(node.left, prefix+"1");
                _walk(node.right, prefix+"0");
            } else {
                codes.emplace(prefix, node.code.value());
            }
        };

        _walk(0, "");

        ofstream flog("log.txt", ios::out);
        for (auto it : codes) {
            flog << " '" << it.first << "': " << it.second << "," << endl;
        }
    }

    int getBit()
    {
        static int n = -1;
        static char c;
        if (n < 0) {
            fin.get(c);
            n = 7;
            //cout << "byte: " << hex << static_cast<int>(c) << endl;
        }
        //cout << "bit: " << ((c >> (n)) & 1) << endl;
        return (c >> (n--)) & 1;
    }

    int getOffsetBits()
    {
        register int n = 12, ret = 0;
        while (n--) {
            ret = (ret << 1) | getBit();
        }
        return ret;
    }

    void decompress(fstream& fout)
    {
        int decCount = head.decCount;
        unique_ptr<char[]> buffer = make_unique<char[]>(head.size);
        char* pBuffer = buffer.get();

        ofstream log("log.txt", ios::out);

        while (decCount--) {
            int nodeIndex = 0;
            while (true) {
                const TreeNode& node = tree[nodeIndex];
                nodeIndex = getBit() ? node.right : node.left;
                //cout << "nodeIndex " << hex << nodeIndex << endl;
                if (tree[nodeIndex].code)
                    break;
            }
            int code = tree[nodeIndex].code.value();
            //cout << code << endl;
            if (code < 256) {
                *pBuffer++ = static_cast<char>(code);
                log << hex << int(code)  << endl;
            } else {
                int count = (code & 0xff) + 2;
                int offset = getOffsetBits() + 2;
                log << hex << ((count-2)|0x100) << ", " << (offset-2) << endl;
                char* pOffset = pBuffer - offset;
                while (count--) {
                    *pBuffer++ = *pOffset++;
                }
            }
        }
        fout.write(buffer.get(), head.size);
    }

    bool load(const string& fileName)
    {
        fin = ifstream(fileName, ios::binary);
        if (!fin.is_open())
            return false;

        fin.read(reinterpret_cast<char*>(&head), sizeof head);

        return true;
    }

    bool save(const string& fileName)
    {
        fstream fout(fileName, ios::out | ios::binary);
        if (! fout.is_open())
            return false;

        vector<LeafNode> leafNodes;
        for (int i = 0; i < 512; i++) {
            static char depth;
            fin.get(depth);
            char key = keyGen();
            depth = depth - key;
            if (depth)
                leafNodes.push_back({ depth, i });
        }

        sort(leafNodes.begin(), leafNodes.end(), [](LeafNode& l, LeafNode& r) {
            return (l.depth != r.depth) ? l.depth < r.depth : l.code < r.code;
        });

        //ofstream flog("log.txt", ios::out);
        //for (auto n : leafNodes) {
        //    flog << hex << "0x" << n.depth << " 0x" << n.code << endl;
        //}
        //flog.close();

        huffmanTree(leafNodes);
        //walkTree();

        ofstream flog("log.txt", ios::out);
        for (auto n : tree) {
            if (n.code)
                flog << "<HuffmanNode (" << n.code.value() << ")>" << endl;
            else if (n.left > 0)
                flog << "<HuffmanNode " << n.left << " " << n.right << ">" << endl;;
        }
        flog.close();

        decompress(fout);
        fout.flush();

        return true;
    }
};


void main()
{
    //unique_ptr<DSC_Decript> dec = make_unique<DSC_Decript>();
    //dec->load("D:\\_PEDIY\\bgi_tool\\arc-writer\\sysgrp\\SGDialog990008");
    //dec->save("D:\\_PEDIY\\bgi_tool\\arc-writer\\sysgrp\\SGDialog990008.dec");

    //unique_ptr<DSC_Encript> enc = make_unique<DSC_Encript>();
    //enc->load("D:\\_PEDIY\\bgi_tool\\arc-writer\\sysgrp\\SGDialog990008.dec");
    //enc->save("D:\\_PEDIY\\bgi_tool\\arc-writer\\sysgrp\\SGDialog990008.enc");

    //int a;
    //cin >> a;

    //int v1 = 1, v2 = 2;

    //int &rv1 = v1;

    //int *pv1 = &rv1;

    //cout << *pv1 << endl;

    int a;
    cin >> a;
}
