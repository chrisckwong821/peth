import json
import difflib
import os


class ContractSource(object):

    def __init__(self, code=None) -> None:
        self.contracts = {}  # name => source
        if code:
            self.parse_source(code)


    def parse_source(self, code: str):
        """
        Split full source code into contracts code.
        Note this method may throw exceptions.
        """

        while True:

            # Find the line which starts with "contract"

            # TODO: library, abstract contract, interface ?
            if not code.startswith('contract'):
                i = code.find('\ncontract')
                if i == -1:
                    # Not contract here.
                    break
                code = code[i + 1:]  # skip \n

            # Find the end of contract.
            count = 0
            end = 0
            for i, c in enumerate(code):
                if c == '{':
                    count += 1

                if c == '}':
                    count -= 1
                    assert count >= 0, "Curly brackets do NOT match"
                    if count == 0:
                        end = i + 1  # skip }
                        break

            contract_code = code[: end]
            contract_name = contract_code[:100].split()[1]

            assert contract_name not in self.contracts, "Same contract name."

            self.contracts[contract_name] = contract_code

            code = code[end:]  # continue.

    def __diff_file(self, a, b, output_filename):
        d = difflib.HtmlDiff()
        buf = d.make_file(a.splitlines(), b.splitlines())
        open(output_filename + '.html', 'w').write(buf)
        print("Written to " + output_filename+'.html')

    def compare(self, other, output=None):

        if output is None:
            output = 'diff'

        if not os.path.isdir(output):
            os.makedirs(output)

        src_left = dict(self.contracts)
        dst_left = dict(other.contracts)

        to_comp = dict(other.contracts)
        for name1, src1, in self.contracts.items():
            if name1 in to_comp:
                src2 = to_comp[name1]
                s = difflib.SequenceMatcher(None, src1, src2)
                similarity = s.ratio()
                filename = "%s_SAMENAME_%0.2f" % (name1, similarity)
                self.__diff_file(src1, src2, os.path.join(output, filename))
                src_left[name1] = None
                dst_left[name1] = None

                # Skip similarity-guided comparison for the contract.
                del to_comp[name1]
                continue 

            for name2, src2 in to_comp.items():
                s = difflib.SequenceMatcher(None, src1, src2)
                similarity = s.ratio()
                filename = "%s_%s_%0.2f" % (name1, name2, similarity)
                # print(filename)
                if similarity > 0.1:
                    self.__diff_file(src1, src2, os.path.join(output, filename))
                    src_left[name1] = None
                    dst_left[name2] = None
        
        src_left_names = list(filter(lambda x: src_left[x], src_left))
        dst_left_names = list(filter(lambda x: dst_left[x], dst_left))
        if src_left_names or dst_left_names:
            print("Non-matched contracts:")
            print(','.join(src_left_names))
            print('-'*10)
            print(','.join(dst_left_names))

        

