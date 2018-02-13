#!/usr/bin/env python
# encoding: utf-8

# 本文件大部分代码及思路来自
# https://github.com/scmsqhn/autohome-spider-qinhaining/blob/master/spider/autohome.py
# 有修改

import re
import traceback


# 从 js 中获取混淆字典
def get_word_list(js):

    # 混淆类型1： 普通的变量定义
    """
    var VB_ = '万中价';
    """
    var_regex = "var\s+(\w+)\s*=\s*(\'[^\']+\');"
    regex = re.compile(var_regex)
    js_functions = regex.findall(js)
    js = re.sub(var_regex, "", js)
    for var_name, var_value in js_functions:
        js = js.replace(var_name, var_value)

    # 混淆类型2： 无参数 if返回常量 else返回函数
    """
    function zX_() {
            function _z() {
                return '09';
            };
            if (_z() == '09,') {
                return 'zX_';
            } else {
                return _z();
            }
        }
    """
    regex = re.compile("""
        function\s+\w+\(\)\s*{\s*
            function\s+\w+\(\)\s*{\s*
                return\s+\'[^\']+\';\s*
            \};\s*
            if\s*\(\w+\(\)\s*==\s*\'[^\']+\'\)\s*{\s*
                return\s*\'[^\']+\';\s*
            \}\s*else\s*{\s*
                return\s*\w+\(\);\s*
            \}\s*
        \}
        """, re.X)
    js_functions = regex.findall(js)
    for js_function in js_functions:
        function_name = re.search("""
        function\s+(\w+\(\))\s*{\s*
            function\s+\w+\(\)\s*{\s*
                return\s+(\'[^\']+\');\s*
            \};\s*
            if\s*\(\w+\(\)\s*==\s*(\'[^\']+\')\)\s*{\s*
                return\s*(\'[^\']+\');\s*
            \}\s*else\s*{\s*
                return\s*\w+\(\);\s*
            \}\s*
        \}
        """, js_function, re.X)
        js = js.replace(js_function, "")
        # 替换全文
        a, b, c, d = function_name.groups()
        if b == c:
            js = js.replace(a, d)
        else:
            js = js.replace(a, b)

    # 混淆类型3： 无参数 if返回函数 else返回常量
    """
    function wu_() {
            function _w() {
                return 'wu_';
            };
            if (_w() == 'wu__') {
                return _w();
            } else {
                return '5%';
            }
        }
    """
    regex = re.compile("""
        function\s+\w+\(\)\s*{\s*
            function\s+\w+\(\)\s*{\s*
                return\s+\'[^\']+\';\s*
            \};\s*
            if\s*\(\w+\(\)\s*==\s*\'[^\']+\'\)\s*{\s*
                return\s*\w+\(\);\s*
            \}\s*else\s*{\s*
                return\s*\'[^\']+\';\s*
            \}\s*
        \}
        """, re.X)
    js_functions = regex.findall(js)
    for js_function in js_functions:
        function_name = re.search("""
        function\s+(\w+\(\))\s*{\s*
            function\s+\w+\(\)\s*{\s*
                return\s+(\'[^\']+\');\s*
            \};\s*
            if\s*\(\w+\(\)\s*==\s*(\'[^\']+\')\)\s*{\s*
                return\s*\w+\(\);\s*
            \}\s*else\s*{\s*
                return\s*(\'[^\']+\');\s*
            \}\s*
        \}
        """, js_function, re.X)
        js = js.replace(js_function, "")
        # 替换全文
        a, b, c, d = function_name.groups()
        if b == c:
            js = js.replace(a, b)
        else:
            js = js.replace(a, d)

    # 混淆类型4
    """
    var Ff_ = function(Ff__) {
            var _F = function(Ff__) {
                    'return Ff_';
                    return Ff__;
                };
            return _F(Ff__);
        };
    """
    regex = re.compile("""
        var\s+\w+\s*=\s*function\(\w+\)\s*{\s*
            var\s+\w+\s*=\s*function\(\w+\)\s*{\s*
                \'return\s+\w+\';
                return\s+\w+;\s*
            \};\s*
            return\s+\w+\(\w+\);\s*
        \};
        """, re.X)
    js_functions = regex.findall(js)
    for js_function in js_functions:
        function_name = re.search("var\s+(\w+)\s*=\s*function\(\w+\)\s*{\s*var\s+\w+\s*=", js_function)
        js = js.replace(js_function, "")
        # 替换全文
        a = function_name.group(1)
        js = re.sub("%s\(([^)]+)\)" % a, r"\1", js)

    # 混淆类型5
    """
    var vs_ = function() {
            'vs_';
            var _v = function() {
                    return '供';
                };
            return _v();
        };
    """
    regex = re.compile("""
        var\s+\w+\s*=\s*function\(\)\s*{\s*
          \'[^\']+\';\s*
            var\s+\w+\s*=\s*function\(\)\s*{\s*
                return\s+\'[^\']+\';\s*
            \};\s*
            return\s+\w+\(\);\s*
        \};
        """, re.X)
    js_functions = regex.findall(js)
    for js_function in js_functions:
        function_name = re.search("var\s+(\w+)\s*=\s*function\(\)\s*{\s*\'[^\']+\';\s*var\s+\w+\s*=\s*function\(\)\s*{\s*return\s+(\'[^\']+\');", js_function)
        js = js.replace(js_function, "")
        # 替换全文
        a, b = function_name.groups()
        js = js.replace("%s()" % a, b)

    # 混淆类型6： 提前声明函数 参数作为函数值返回
    """
    var ZA_ = function(ZA__) {
            'return ZA_';
            return ZA__;
        };
    """
    regex = re.compile("var\s+\w+\s*=\s*function\(\w+\)\s*{\s*\'return\s+\w+\';\s*return\s+\w+;\s*\};")
    js_functions = regex.findall(js)
    for js_function in js_functions:
        function_name = re.search("var\s+(\w+)", js_function)
        js = js.replace(js_function, "")
        # 替换全文
        a = function_name.group(1)
        js = re.sub("%s\(([^)]+)\)" % a, r"\1", js)

    # 混淆类型7： 提前声明函数 无参数 返回常量
    """
    var Qh_ = function() {
            'return Qh_';
            return ';';
        };
    """
    regex = re.compile("""
            var\s+\w+\s*=\s*function\(\)\s*{\s*
                \'return\s+\w+\';\s*
                return\s+\'[^\']+\';\s*
                \};
            """, re.X)
    js_functions = regex.findall(js)
    for js_function in js_functions:
        function_name = re.search("""
            var\s+(\w+)\s*=\s*function\(\)\s*{\s*
                \'return\s+\w+\';\s*
                return\s+(\'[^\']+\');\s*
                \};
            """, js_function, re.X)
        js = js.replace(js_function, "")
        # 替换全文
        a, b = function_name.groups()
        js = js.replace("%s()" % a, b)

    # 混淆类型8： 无参数函数 返回常量
    """
    function ZP_() {
            'return ZP_';
            return 'E';
        }
    """
    regex = re.compile("""
            function\s*\w+\(\)\s*{\s*
                \'return\s*[^\']+\';\s*
                return\s*\'[^\']+\';\s*
            \}
        """, re.X)
    js_functions = regex.findall(js)
    for js_function in js_functions:
        function_name = re.search("""
            function\s*(\w+\(\))\s*{\s*
                \'return\s*[^\']+\';\s*
                return\s*(\'[^\']+\');\s*
            \}
        """, js_function, re.X)
        js = js.replace(js_function, "")
        # 替换全文
        a, b = function_name.groups()
        js = js.replace(a, b)

    # 混淆类型9： 字符串拼接时使用的匿名 无参数 返回常量函数
    """
    (function() {
                'return sZ_';
                return '1'
            })()
    """
    regex = re.compile("""
            \(function\(\)\s*{\s*
                \'return\s*[^\']+\';\s*
                return\s*\'[^\']*\';?
            \}\)\(\)
        """, re.X)
    js_functions = regex.findall(js)
    for js_function in js_functions:
        function_name = re.search("""
            \(function\(\)\s*{\s*
                \'return\s*[^\']+\';\s*
                return\s*(\'[^\']*\');?
            \}\)\(\)
        """, js_function, re.X)
        js = js.replace(js_function, function_name.group(1))

    # 混淆类型10： 字符串拼接时使用的有参数匿名函数 参数作为函数值返回
    """
    (function(iU__) {
                'return iU_';
                return iU__;
            })('9F')
    """
    regex = re.compile("""
            \(function\(\w+\)\s*{\s*
                \'return\s*[^\']+\';\s*
                return\s*\w+;\s*
            \}\)\(\'[^\']*\'\)
        """, re.X)
    js_functions = regex.findall(js)
    for js_function in js_functions:
        function_name = re.search("""
            \(function\(\w+\)\s*{\s*
                \'return\s*[^\']+\';\s*
                return\s*\w+;\s*
            \}\)\((\'[^\']*\')\)
        """, js_function, re.X)
        js = js.replace(js_function, function_name.group(1))

    # 组合字符串
    js = js.replace("'+'", "")

    # 文字串
    regex = re.compile("decodeURIComponent\'\]\(\'([^\']+)\'")
    str_words = regex.search(js).group(1)

    # 文字索引串
    regex = re.compile("\$rulePosList\$=\$Split\$\(\(\$SystemFunction1\$\(\'\'\)\+\'([\d,;]+)\'")
    str_indexes = regex.search(js).group(1)

    word_list = []
    word_indexes_list = str_indexes.split(';')
    for one_word_indexes in word_indexes_list:
        word = ''
        indexes = one_word_indexes.split(',')
        for index in indexes:
            word = word + str_words[int(index)]
        word_list.append(word)

    return word_list


# html 全文反混淆
def get_complete_text(text):
    js_types = re.findall('hs_kw\d+_([^\'\"]+)', text)
    js_types = set(js_types)

    js_list = re.findall("<script>(\(function[\s\S]+?)\(document\);</script>", text)

    word_list_dict = {}
    for js in js_list:
        if not js:
            continue

        try:
            word_list = get_word_list(js)
        except Exception as e:
            traceback.print_exc()
            continue

        for js_type in js_types:
            if js_type in js:
                break
        else:
            continue

        word_list_dict.update({js_type: word_list})

    def char_replace(m):
        index = int(m.group(1))
        js_type = m.group(2)
        word_list = word_list_dict.get(js_type, [])
        if not word_list:
            return m.group()
        char = word_list[index]
        return char

    text = re.sub("<span\s*class=[\'\"]hs_kw(\d+)_([^\'\"]+)[\'\"]></span>", char_replace, text)
    return text
