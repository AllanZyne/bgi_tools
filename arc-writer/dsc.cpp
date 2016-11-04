
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
#include <functional>

//#include <Magick++.h>

#include "optional.hpp"


using namespace std;
using namespace std::experimental;

//using namespace Magick;


typedef pair<int, int> CodesPair;

template<>
struct less<CodesPair>
{
	bool operator()(const CodesPair& left, const CodesPair& right)
	{
		return left.first != right.first ? left.first < right.first : left.second < right.second;
	}
};


class TreeNode {
    static int NodeIndex;
	int index;

public:

	TreeNode* left;
	TreeNode* right;
	int code;

	TreeNode(int code)
		: code(code)
        , left(nullptr)
        , right(nullptr)
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

	bool operator<(const TreeNode& node) const
	{
        return index < node.index;
	}
};

int TreeNode::NodeIndex = 0;


struct FreqPair
{
	unsigned freq;
	TreeNode* node;

	FreqPair(unsigned freq, TreeNode* node)
		: freq(freq), node(node)
	{
	}
};

//int Freqs[0x200];
list<int> Freqs;

template<>
struct less<FreqPair>
{
    // freq 最小， node 最大
	bool operator()(const FreqPair& left, const FreqPair& right)
	{
		return (left.freq != right.freq) ? (left.freq > right.freq) : ((*left.node) < (*right.node));
        //return (left.freq != right.freq) ? (left.freq > right.freq) : (left.node->code < right.node->code);
	}
};


class ofsbitstream : public ofstream {
	char m_bit_buf = 0;
	size_t m_aval_bits = 8;
	bool m_closed = false;
public:
    using ofstream::ofstream;

	~ofsbitstream()
	{
		if (!m_closed)
			close();
	}

    using ofstream::write;

	void write(size_t bits, size_t value) {
        register char _value = 0;
        if (bits <= m_aval_bits) {
            m_aval_bits -= bits;

            _value = value & ((1 << bits)-1);
            //value >>= bits;

            m_bit_buf |= _value << m_aval_bits;
            if (! m_aval_bits) {
                put(m_bit_buf);
                m_bit_buf = 0;
                m_aval_bits = 8;
            }
        } else {
            bits -= m_aval_bits;

            _value = (value >> bits) & ((1 << m_aval_bits)-1);
            m_aval_bits = 0;
            _value |= m_bit_buf;
            put(_value);

            if (bits < 8) // #1
                goto end;

            bits -= 8;
            _value = (value >> bits) & 0xff;
            put(_value);

            if (bits < 8) // #2
                goto end;

            bits -= 8;
            _value = (value >> bits) & 0xff;
            put(_value);

            if (bits < 8) // #3
                goto end;

            bits -= 8;
            _value = (value >> bits) & 0xff;
            put(_value);

            if (bits < 8) // #4
                goto end;

            bits -= 8;
            _value = (value >> bits) & 0xff;
            put(_value);
        end:
            if (bits) {
                m_aval_bits = 8 - bits;
                _value = value & ((1 << bits)-1);
                m_bit_buf = _value << m_aval_bits;
            } else {
                m_bit_buf = 0;
                m_aval_bits = 8;
            }
        }
	}

	virtual void close() {
		flush_end();
		ofstream::close();
		m_closed = true;
	}

private:
	void flush_end() {
		if (m_aval_bits < 8) {
			put(m_bit_buf);
		}
	}
};


class DSC_Encript {
    struct DSC_Head {
        // 'DSC FORMAT 1.00\0'
        char magic[0x10] = { 'D', 'S', 'C', ' ',
            'F', 'O', 'R', 'M', 'A', 'T', ' ',
            '1', '.', '0', '0', '\0' };
        unsigned key = 0xdeadbeef;
        unsigned size;
        unsigned decCount;
        int reserved = 0;

        DSC_Head(unsigned size, unsigned decCount)
            : size(size), decCount(decCount)
        {
        }
    };

    struct LeafNode {
        int depth;
        int code;
    };


    struct CompressPair {
        int code;
        optional<int> offset;
    };

#define MATCH_MAX 0xff
#define WINDOW_BIT 12
#define WINDOW_SIZE (1 << 12)

    char *window;
    char *pCur0, *pEnd0, *pCur;

	ifstream fin;
	list<char*> hashTable[0x10000];

	struct CodePair {
		int code = 0;
		int depth = 0;
	};
	CodePair codes[0x200];

    size_t fileSize;

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
#ifdef _DEBUG
        ofstream log("enc-codes.txt", ios_base::out);
        log << dec << "" << int((unsigned char)*pCur) << endl;
#endif
        out.push_back({ (*pCur) & 0xff, nullopt });
        if (pCur + 1 == pEnd0) {
            return;
        }
        pCur += 2;

        while (pCur < pEnd0 ) {
            static int size, pos;
            size = pos = -1;
            longestMatch(size, pos);
            if (size < 0) {
#ifdef _DEBUG
                log << dec << "" << int((unsigned char)*(pCur-1)) << endl;
#endif
                out.push_back({ (*(pCur-1)) & 0xff, nullopt });
                putHTable(pCur);
                pCur++;
            } else {
#ifdef _DEBUG
                log << dec << "" <<  (size | 0x100) << ", " << pos << endl;
#endif
                out.push_back({ (size & 0xff) | 0x100, pos });
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
            fileSize = static_cast<size_t>(fin.tellg());
            fin.seekg(0, ios_base::beg);
            if (! fileSize)
                return false;
            window = new char[fileSize];
            fin.read(window, fileSize);
            pCur0 = pCur = window;
            pEnd0 = window + fin.gcount();

        //}
        return true;
    }

  	void walkTree(TreeNode* root)
    {
        //Image image("20480x600", "white");

        //image.strokeColor("black");
        //image.strokeWidth(1);
        //image.strokeAntiAlias(true);

        //function<void(TreeNode*, int, int, int, int, int, int)> _drawWalk =
        //    [&_drawWalk, &image]
        //    (TreeNode* node, int depth, int x, int y, int w, int px, int py) {
        //    //cout << node->code << ":" << depth << endl;
        //    if (node->code < 0) {
        //        _drawWalk(node->left, depth + 1, x - w / 2, y + 30, w / 2, x, y);
        //        _drawWalk(node->right, depth + 1, x + w / 2, y + 30, w / 2, x, y);

        //        image.fillColor("green");
        //        image.draw(DrawableCircle(x, y, x - 5, y));
        //        image.draw(DrawableLine(px, py, x, y));
        //    } else {
        //        image.fillColor("red");
        //        image.draw(DrawableCircle(x, y, x - 2, y));
        //        image.draw(DrawableLine(px, py, x, y));
        //        //image.draw(DrawableText(x, y, to_string(node->code)));
        //    }
        //};

        //_drawWalk(root, 0, 10240, 20, 10240, 10240, 20);

        //image.write("hufftree2.png");

        priority_queue<CodesPair> codesQueue;

        function<void(TreeNode*, int)> _walk = [&_walk, &codesQueue](TreeNode* node, int depth) {
            //cout << node->code << ":" << depth << endl;
            if (node->code < 0) {
                _walk(node->left, depth+1);
                _walk(node->right, depth+1);
            } else {
                //codesQueue.put(make_pair(prefix, node->code));
				codesQueue.emplace(depth, node->code);
            }
			delete node;
        };

        _walk(root, 0);

        auto print = [](int code, int length) {
            string s;
            while (length--) {
                s += (code >> length) & 1 ? '1' : '0';
            }
            return s;
        };


#ifdef _DEBUG
        ofstream log("log-tree2.txt", ios_base::out);
#endif

		int canDepth = codesQueue.top().first, canCode = 0, canCount = 0;
		while (!codesQueue.empty()) {
			CodesPair p = codesQueue.top();
			if (p.first == canDepth) {
				auto & cp = codes[p.second];
				cp.code = canCode + canCount;
				cp.depth = canDepth;
                cp.code = ~cp.code;  // hot fix!
#ifdef _DEBUG
                log << " '" << print(cp.code, cp.depth) << "': " << p.second << "," << endl;
#endif
                canCount++;
                codesQueue.pop();
			} else {
				canCode = (canCode + canCount + 1) >> 1;
				canCount = 0;
				canDepth--;
			}
		}
    }

    void huffmanEncoding(unsigned freqs[0x200])
    {
        priority_queue<FreqPair> freqs_queue;

        for (int i = 0; i < 0x200; i++) {
            if (freqs[i] > 0)
                freqs_queue.emplace(freqs[i], new TreeNode(i));
        }

        //vector<FreqPair> freqs_queue;
        //for (int i = 0; i < 0x200; i++) {
        //    if (freqs[i] > 0)
        //        freqs_queue.emplace_back(freqs[i], new TreeNode(i));
        //}

        //auto cmp = [](FreqPair& left, FreqPair& right) {
        //    return left.freq != right.freq ? left.freq < right.freq : left.node->code > right.node->code;
        //    //return left.freq < right.freq;
        //};
        //sort(freqs_queue.begin(), freqs_queue.end(), cmp);

        while (freqs_queue.size() > 1) {
            FreqPair l = freqs_queue.top();
            freqs_queue.pop();
            FreqPair r = freqs_queue.top();
            freqs_queue.pop();
            freqs_queue.emplace(l.freq + r.freq, new TreeNode(l.node, r.node));
        }

        TreeNode* root = freqs_queue.top().node;
		walkTree(root); // by the way, delete treeNodes
    }

    bool save(const string& fileName)
    {
        vector<CompressPair> out;
        compress(out);

        unsigned freqs[0x200] = { 0 };
        for (auto& p : out) {
            freqs[p.code]++;
        }

		huffmanEncoding(freqs);

		// TODO: bit stream
        ofsbitstream fout(fileName, ios_base::binary);

        DSC_Head head(fileSize, out.size());
        fout.write(reinterpret_cast<char*>(&head), sizeof head);

        auto keyGen = [](unsigned int& key) -> char {
            register unsigned a = (key & 0xffff) * 20021;
            register unsigned b = (key >> 16) * 20021;
            register unsigned c = (key * 346 + b) + (a >> 16);
            key = ((c & 0xffff) << 16) + (a & 0xffff) + 1;
            return c & 0xff;
        };

#ifdef _DEBUG
        ofstream log("enc-depth.txt");
#endif

        for (auto& code : codes) {
            char key = keyGen(head.key);
            char depth = code.depth + key;
            fout.put(depth);
#ifdef _DEBUG
            log << code.depth << endl;
#endif
        }

        for (auto& o : out) {
            auto& code = codes[o.code];
            fout.write(code.depth, code.code);
            if (o.offset) {
                fout.write(12, o.offset.value());
            }
        }

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
        DSC_Decript::get_bit_n = -1;
    }

    char keyGen(unsigned int& key)
    {
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
                _walk(node.left, prefix+"0");
                _walk(node.right, prefix+"1");
            } else {
                codes.emplace(prefix, node.code.value());
            }
        };

        _walk(0, "");

        //Image image("20480x600", "white");

        //image.strokeColor("black");
        //image.strokeWidth(1);
        //image.strokeAntiAlias(true);

        //function<void(int, string, int, int, int, int, int)> _drawWalk =
        //    [this, &_drawWalk, &codes, &image]
        //    (int n, const string& prefix, int x, int y, int w, int px, int py) {
        //    TreeNode& node = tree[n];
        //    if (!node.code) {
        //        _drawWalk(node.left, prefix + "1", x - w/2, y + 50, w/2, x, y);
        //        _drawWalk(node.right, prefix + "0", x + w/2, y + 50, w/2, x, y);

        //        image.fillColor("green");
        //        image.draw(DrawableCircle(x, y, x - 5, y));
        //        image.draw(DrawableLine(px, py, x, y));
        //    } else {
        //        codes.emplace(prefix, node.code.value());

        //        image.fillColor("red");
        //        image.draw(DrawableCircle(x, y, x - 3, y));

        //        //image.draw(DrawableText(x, y, to_string(node.code.value())));
        //        image.draw(DrawableLine(px, py, x, y));
        //    }
        //};

        //_drawWalk(0, "", 10240, 20, 10240, 10240, 20);

        //image.write("hufftree.png");
#ifdef _DEBUG
        ofstream flog("log-tree.txt", ios::out);
        for (auto it : codes) {
            flog << " '" << it.first << "': " << it.second << "," << endl;
        }
#endif
        auto it = codes.begin();
        for (int i = 0; it != codes.end(); i++) {
            Freqs.push_back(it->second);
            it++;
        }
    }

    static int get_bit_n;

    int getBit()
    {
        static char c;
        if (get_bit_n < 0) {
            fin.get(c);
            get_bit_n = 7;
            //cout << "byte: " << hex << static_cast<int>(c) << endl;
        }
        //cout << "bit: " << ((c >> (n)) & 1) << endl;
        return (c >> (get_bit_n--)) & 1;
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

#ifdef _DEBUG
        ofstream log("dec-codes.txt", ios::out);
#endif

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
            //Freqs[code]++;
            if (code < 256) {
                *pBuffer++ = static_cast<char>(code);
#ifdef _DEBUG
                log << hex << int(code)  << endl;
#endif
            } else {
                int count = (code & 0xff) + 2;
                int offset = getOffsetBits() + 2;
#ifdef _DEBUG
                log << hex << ((count-2)|0x100) << ", " << (offset-2) << endl;
#endif
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
#ifdef _DEBUG
        ofstream log("dec-depth.txt");
#endif
        vector<LeafNode> leafNodes;
        for (int i = 0; i < 512; i++) {
            static char depth;
            fin.get(depth);
            char key = keyGen(head.key);
            depth = (unsigned char) depth - key;
#ifdef _DEBUG
            log << (int)depth << endl;
#endif
            if (depth)
                leafNodes.push_back({ depth, i });
        }
#ifdef _DEBUG
        log.close();
#endif
        sort(leafNodes.begin(), leafNodes.end(), [](LeafNode& l, LeafNode& r) {
            return (l.depth != r.depth) ? l.depth < r.depth : l.code < r.code;
        });

        huffmanTree(leafNodes);
        walkTree();

        decompress(fout);
        fout.flush();

        return true;
    }
};

int DSC_Decript::get_bit_n = -1;


void compareBinany(const string& file1, const string& file2)
{
    ifstream f1(file1), f2(file2);
    char c1, c2;

    while (true) {
        f1.get(c1);
        f2.get(c2);
        if (c1 != c2) {
            cout << "!!!!!!" << endl;
            return;
        }
        if (f1.eof() || f2.eof())
            break;
    }
    if (f1.eof() != f2.eof())
        cout << "!!!!!" << endl;
}


void test_bitsstream() {
    ofsbitstream fout("test.bin", ios::binary);
    fout.write(12, 0xf);
    fout.write(12, 0xfef);
    fout.write(4, 0xef);
    fout.write(16, 0xabcd);
    fout.write(2, 0xf);
    fout.write(2, 0x0);
    fout.write(32, 0xefaefaef);
    fout.close();

    ifstream fin("test.bin", ios_base::binary);
    char c = fin.get();
}


void main(int *argc, char **argv)
{
    //InitializeMagick(*argv);

    string fileName = "D:\\_PEDIY\\bgi_tool\\arc-writer\\sysgrp\\SGLogWnd990000";

    cout << "DEC" << endl;
    unique_ptr<DSC_Decript> dec = make_unique<DSC_Decript>();
    if (dec->load(fileName))
        dec->save(fileName + ".dec");

    cout << "ENC" << endl;
    unique_ptr<DSC_Encript> enc = make_unique<DSC_Encript>();
    if (enc->load(fileName + ".dec"))
        enc->save(fileName + ".enc");

    cout << "DEC2" << endl;
    unique_ptr<DSC_Decript> dec2 = make_unique<DSC_Decript>();
    if (dec2->load(fileName + ".enc"))
        dec2->save(fileName + ".dec2");

    cout << "CMP" << endl;
    compareBinany(fileName + ".dec", fileName + ".dec2");

    cout << "ENC2" << endl;
    unique_ptr<DSC_Encript> enc2 = make_unique<DSC_Encript>();
    if (enc2->load(fileName + ".dec"))
        enc2->save(fileName + ".enc");

    cout << "CMP2" << endl;
    compareBinany(fileName + ".dec", fileName + ".dec2");



    int a;
    cin >> a;

}
