# -*- coding: utf-8 -*-
"""
    pygments.lexers.asm
    ~~~~~~~~~~~~~~~~~~~

    Lexers for assembly languages.

    :copyright: Copyright 2006-2015 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from pygments.lexer import RegexLexer, include, bygroups, using, DelegatingLexer
from pygments.lexers.c_cpp import CppLexer, CLexer
from pygments.lexers.d import DLexer
from pygments.token import Text, Name, Number, String, Comment, Punctuation, \
    Other, Keyword, Operator

__all__ = ['GasLexer', 'ObjdumpLexer', 'DObjdumpLexer', 'CppObjdumpLexer',
           'CObjdumpLexer', 'HsailLexer', 'LlvmLexer', 'NasmLexer', 'NasmObjdumpLexer',
           'Ca65Lexer']


class GasLexer(RegexLexer):
    """
    For Gas (AT&T) assembly code.
    """
    name = 'GAS'
    aliases = ['gas', 'asm']
    filenames = ['*.s', '*.S']
    mimetypes = ['text/x-gas']

    #: optional Comment or Whitespace
    string = r'"(\\"|[^"])*"'
    char = r'[\w$.@-]'
    identifier = r'(?:[a-zA-Z$_]' + char + '*|\.' + char + '+)'
    number = r'(?:0[xX][a-zA-Z0-9]+|\d+)'

    tokens = {
        'root': [
            include('whitespace'),
            (identifier + ':', Name.Label),
            (r'\.' + identifier, Name.Attribute, 'directive-args'),
            (r'lock|rep(n?z)?|data\d+', Name.Attribute),
            (identifier, Name.Function, 'instruction-args'),
            (r'[\r\n]+', Text)
        ],
        'directive-args': [
            (identifier, Name.Constant),
            (string, String),
            ('@' + identifier, Name.Attribute),
            (number, Number.Integer),
            (r'[\r\n]+', Text, '#pop'),

            (r'#.*?$', Comment, '#pop'),

            include('punctuation'),
            include('whitespace')
        ],
        'instruction-args': [
            # For objdump-disassembled code, shouldn't occur in
            # actual assembler input
            ('([a-z0-9]+)( )(<)('+identifier+')(>)',
                bygroups(Number.Hex, Text, Punctuation, Name.Constant,
                         Punctuation)),
            ('([a-z0-9]+)( )(<)('+identifier+')([-+])('+number+')(>)',
                bygroups(Number.Hex, Text, Punctuation, Name.Constant,
                         Punctuation, Number.Integer, Punctuation)),

            # Address constants
            (identifier, Name.Constant),
            (number, Number.Integer),
            # Registers
            ('%' + identifier, Name.Variable),
            # Numeric constants
            ('$'+number, Number.Integer),
            (r"$'(.|\\')'", String.Char),
            (r'[\r\n]+', Text, '#pop'),
            (r'#.*?$', Comment, '#pop'),
            include('punctuation'),
            include('whitespace')
        ],
        'whitespace': [
            (r'\n', Text),
            (r'\s+', Text),
            (r'#.*?\n', Comment)
        ],
        'punctuation': [
            (r'[-*,.():]+', Punctuation)
        ]
    }

    def analyse_text(text):
        if re.match(r'^\.(text|data|section)', text, re.M):
            return True
        elif re.match(r'^\.\w+', text, re.M):
            return 0.1


def _objdump_lexer_tokens(asm_lexer):
    """
    Common objdump lexer tokens to wrap an ASM lexer.
    """
    hex_re = r'[0-9A-Za-z]'
    return {
        'root': [
            # File name & format:
            ('(.*?)(:)( +file format )(.*?)$',
                bygroups(Name.Label, Punctuation, Text, String)),
            # Section header
            ('(Disassembly of section )(.*?)(:)$',
                bygroups(Text, Name.Label, Punctuation)),
            # Function labels
            # (With offset)
            ('('+hex_re+'+)( )(<)(.*?)([-+])(0[xX][A-Za-z0-9]+)(>:)$',
                bygroups(Number.Hex, Text, Punctuation, Name.Function,
                         Punctuation, Number.Hex, Punctuation)),
            # (Without offset)
            ('('+hex_re+'+)( )(<)(.*?)(>:)$',
                bygroups(Number.Hex, Text, Punctuation, Name.Function,
                         Punctuation)),
            # Code line with disassembled instructions
            ('( *)('+hex_re+r'+:)(\t)((?:'+hex_re+hex_re+' )+)( *\t)([a-zA-Z].*?)$',
                bygroups(Text, Name.Label, Text, Number.Hex, Text,
                         using(asm_lexer))),
            # Code line with ascii
            ('( *)('+hex_re+r'+:)(\t)((?:'+hex_re+hex_re+' )+)( *)(.*?)$',
                bygroups(Text, Name.Label, Text, Number.Hex, Text, String)),
            # Continued code line, only raw opcodes without disassembled
            # instruction
            ('( *)('+hex_re+r'+:)(\t)((?:'+hex_re+hex_re+' )+)$',
                bygroups(Text, Name.Label, Text, Number.Hex)),
            # Skipped a few bytes
            (r'\t\.\.\.$', Text),
            # Relocation line
            # (With offset)
            (r'(\t\t\t)('+hex_re+r'+:)( )([^\t]+)(\t)(.*?)([-+])(0x'+hex_re+'+)$',
                bygroups(Text, Name.Label, Text, Name.Property, Text,
                         Name.Constant, Punctuation, Number.Hex)),
            # (Without offset)
            (r'(\t\t\t)('+hex_re+r'+:)( )([^\t]+)(\t)(.*?)$',
                bygroups(Text, Name.Label, Text, Name.Property, Text,
                         Name.Constant)),
            (r'[^\n]+\n', Other)
        ]
    }


class ObjdumpLexer(RegexLexer):
    """
    For the output of 'objdump -dr'
    """
    name = 'objdump'
    aliases = ['objdump']
    filenames = ['*.objdump']
    mimetypes = ['text/x-objdump']

    tokens = _objdump_lexer_tokens(GasLexer)


class DObjdumpLexer(DelegatingLexer):
    """
    For the output of 'objdump -Sr on compiled D files'
    """
    name = 'd-objdump'
    aliases = ['d-objdump']
    filenames = ['*.d-objdump']
    mimetypes = ['text/x-d-objdump']

    def __init__(self, **options):
        super(DObjdumpLexer, self).__init__(DLexer, ObjdumpLexer, **options)


class CppObjdumpLexer(DelegatingLexer):
    """
    For the output of 'objdump -Sr on compiled C++ files'
    """
    name = 'cpp-objdump'
    aliases = ['cpp-objdump', 'c++-objdumb', 'cxx-objdump']
    filenames = ['*.cpp-objdump', '*.c++-objdump', '*.cxx-objdump']
    mimetypes = ['text/x-cpp-objdump']

    def __init__(self, **options):
        super(CppObjdumpLexer, self).__init__(CppLexer, ObjdumpLexer, **options)


class CObjdumpLexer(DelegatingLexer):
    """
    For the output of 'objdump -Sr on compiled C files'
    """
    name = 'c-objdump'
    aliases = ['c-objdump']
    filenames = ['*.c-objdump']
    mimetypes = ['text/x-c-objdump']

    def __init__(self, **options):
        super(CObjdumpLexer, self).__init__(CLexer, ObjdumpLexer, **options)


class HsailLexer(RegexLexer):
    """
    For HSAIL assembly code.
    """
    name = 'HSAIL'
    aliases = ['hsail', 'hsa']
    filenames = ['*.hsail']
    mimetypes = ['text/x-hsail']

    string = r'"[^"]*?"'
    identifier = r'[a-zA-Z_][a-zA-Z0-9_.]*'
    # Registers
    register_number = r'[0-9]+'
    register = r'(\$(c|s|d|q)' + register_number + ')'
    # Qualifiers
    alignQual = r'(align\(\d+\))'
    widthQual = r'(width\((\d+|all)\))'
    allocQual = r'(alloc\(agent\))'
    # Instruction Modifiers
    roundingMod = (r'((_ftz)?(_up|_down|_zero|_near))')
    datatypeMod =  (r'_(' 
                    # baseTypes
                    r'u8|s8|u16|s16|u32|s32|u64|s64'
                    r'|b1|b8|b16|b32|b64|b128'
                    r'|f16|f32|f64' 
                    # packedTypes
                    r'|u8x4| s8x4| u16x2| s16x2| u8x8| s8x8| u16x4| s16x4| u32x2| s32x2| u8x16| s8x16| u16x8| s16x8| u32x4| s32x4| u64x2| s64x2'
                    r'|f16x2| f16x4| f16x8'
                    r'|f32x2| f32x4'
                    r'|f64x2'
                    # opaqueType
                    r'|roimg| woimg| rwimg'
                    r'|samp'
                    r'|sig32| sig64'
                    r')')
                    
    # Numeric Constant
    float = r'((\d+\.)|(\d*\.\d+))[eE][+-]?\d+'
    hexfloat = r'0[xX](([0-9a-fA-F]+\.[0-9a-fA-F]*)|([0-9a-fA-F]*\.[0-9a-fA-F]+))[pP][+-]?\d+'
    ieeefloat= r'0((h|H)[0-9a-fA-F]{4}|(f|F)[0-9a-fA-F]{8}|(d|D)[0-9a-fA-F]{16})'
    
    tokens = {
        'root': [
            include('whitespace'),
            include('comments'),
            
            (string, String),

            (r'@' + identifier + ':', Name.Label),

            (register, Name.Variable.Anonymous),
            
            include('keyword'),
            
            (r'&' + identifier, Name.Variable.Global),
            (r'%' + identifier, Name.Variable),
            
            (hexfloat, Number.Hex),
            (r'0[xX][a-fA-F0-9]+', Number.Hex),
            (ieeefloat, Number.Float),
            (float, Number.Float),
            ('\d+', Number.Integer),

            (r'[=<>{}\[\]()*.,:;!]|x\b', Punctuation)
        ],
        'whitespace': [
            (r'(\n|\s)+', Text),
        ],
        'comments': [
            (r'/\*.*?\*/', Comment.Multiline),
            (r'//.*?\n', Comment.Singleline),
        ],
        'keyword': [
            # Types
            (r'kernarg'+datatypeMod,
             Keyword.Type),
        
            # Regular keywords
            (r'(\$full|\$base'
             r'|\$small|\$large'
             r'|\$default|\$zero|\$near)', Keyword),
            (r'(module|extension'
             r'|pragma'
             r'|prog|indirect|signature|decl'
             r'|kernel|function'
             r'|enablebreakexceptions|enabledetectexceptions|maxdynamicgroupsize|maxflatgridsize|maxflatworkgroupsize|requireddim|requiredgridsize|requiredworkgroupsize|requirenopartialworkgroups'
             r')\b', Keyword),

             # instructions
             (roundingMod, Keyword), 
             (datatypeMod, Keyword), 
             (r'_(' + alignQual + '|' + widthQual + ')', Keyword), 
             (r'_kernarg', Keyword), 
             (r'(nop|imagefence)\b', Keyword), 
             (r'(cleardetectexcept|clock|cuid|debugtrap|dim|getdetectexcept|groupbaseptr|kernargbaseptr|laneid|maxcuid|maxwaveid|packetid|setdetectexcept|waveid|workitemflatabsid|workitemflatid|nullptr'
             r'|abs|bitrev|currentworkgroupsize|currentworkitemflatid|fract|ncos|neg|nexp2|nlog2|nrcp|nrsqrt|nsin|nsqrt|gridgroups|gridsize|not|sqrt|workgroupid|workgroupsize|workitemabsid|workitemid'
             r'|ceil|floor|rint|trunc'
             r'|add|bitmask|borrow|carry|copysign|div|rem|sub|shl|shr|and|or|xor|unpackhi|unpacklo'
             r'|max|min'
             r'|fma|mad|bitextract|bitselect|shuffle|cmov|bitalign|bytealign|lerp|nfma'
             r'|mul|mulhi|mul24hi|mul24|mad24|mad24hi|bitinsert|combine|expand|lda|mov'
             r'|pack|unpack|packcvt|unpackcvt|sad|sementp|ftos|stof'
             r'|cmp|ld|st'
             r'|_eq|_ne|_lt|_le|_gt|_ge|_equ|_neu|_ltu|_leu|_gtu|_geu|_num|_nan|_seq|_sne|_slt|_sle|_sgt|_sge|_snum|_snan|_sequ|_sneu|_sltu|_sleu|_sgtu|_sgeu'
             r'|atomic|_ld|_st|_cas|_add|_and|_exch|_max|_min|_or|_sub|_wrapdec|_wrapinc|_xor'
             r'|ret|cvt'
             r'|_readonly|_kernarg|_global'
             
             r'|br|cbr|sbr'           
             r'_scacq|_screl|_scar|_rlx'
             r'_wave|_wg|_agent|_system'
             r'|ldimage|stimage'
             r'|_v2|_v3|_v4'
             r'|_1d|_2d|_3d|_1da|_2da|_1db|_2ddepth|_2dadepth'
             r'|_width|_height|_depth|_array|_channelorder|_channeltype'
             r'|querysampler|_coord|_filter|_addressing'
             r'|barrier|wavebarrier'
             r'|initfbar|joinfbar|waitfbar|arrivefbar|leavefbar|releasefbar|ldf'
             r'|activelaneid|activelanecount|activelanemask|activelanepermute'
             r'|call|scall|icall'
             r'|alloca|packetcompletionsig'
             r'|addqueuewriteindex|casqueuewriteindex|ldqueuereadindex|stqueuereadindex'
             r'|readonly|global|private|group|spill|arg'
             r'|_upi|_downi|_zeroi|_neari|_upi_sat|_downi_sat|_zeroi_sat|_neari_sat|_supi|_sdowni|_szeroi|_sneari|_supi_sat|_sdowni_sat|_szeroi_sat|_sneari_sat'
             r'|_pp|_ps|_sp|_ss|_s|_p|_pp_sat|_ps_sat|_sp_sat|_ss_sat|_s_sat|_p_sat'
             r')', Keyword),
             
              
            # Integer types
            (r'i[1-9]\d*', Keyword)
        ]
    }
    
class LlvmLexer(RegexLexer):
    """
    For LLVM assembly code.
    """
    name = 'LLVM'
    aliases = ['llvm']
    filenames = ['*.ll']
    mimetypes = ['text/x-llvm']

    #: optional Comment or Whitespace
    string = r'"[^"]*?"'
    identifier = r'([-a-zA-Z$._][\w\-$.]*|' + string + ')'

    tokens = {
        'root': [
            include('whitespace'),

            # Before keywords, because keywords are valid label names :(...
            (identifier + '\s*:', Name.Label),

            include('keyword'),

            (r'%' + identifier, Name.Variable),
            (r'@' + identifier, Name.Variable.Global),
            (r'%\d+', Name.Variable.Anonymous),
            (r'@\d+', Name.Variable.Global),
            (r'#\d+', Name.Variable.Global),
            (r'!' + identifier, Name.Variable),
            (r'!\d+', Name.Variable.Anonymous),
            (r'c?' + string, String),

            (r'0[xX][a-fA-F0-9]+', Number),
            (r'-?\d+(?:[.]\d+)?(?:[eE][-+]?\d+(?:[.]\d+)?)?', Number),

            (r'[=<>{}\[\]()*.,!]|x\b', Punctuation)
        ],
        'whitespace': [
            (r'(\n|\s)+', Text),
            (r';.*?\n', Comment)
        ],
        'keyword': [
            # Regular keywords
            (r'(begin|end'
             r'|true|false'
             r'|declare|define'
             r'|global|constant'

             r'|private|linker_private|internal|available_externally|linkonce'
             r'|linkonce_odr|weak|weak_odr|appending|dllimport|dllexport'
             r'|common|default|hidden|protected|extern_weak|external'
             r'|thread_local|zeroinitializer|undef|null|to|tail|target|triple'
             r'|datalayout|volatile|nuw|nsw|nnan|ninf|nsz|arcp|fast|exact|inbounds'
             r'|align|addrspace|section|alias|module|asm|sideeffect|gc|dbg'
             r'|linker_private_weak'
             r'|attributes|blockaddress|initialexec|localdynamic|localexec'
             r'|prefix|unnamed_addr'

             r'|ccc|fastcc|coldcc|x86_stdcallcc|x86_fastcallcc|arm_apcscc'
             r'|arm_aapcscc|arm_aapcs_vfpcc|ptx_device|ptx_kernel'
             r'|intel_ocl_bicc|msp430_intrcc|spir_func|spir_kernel'
             r'|x86_64_sysvcc|x86_64_win64cc|x86_thiscallcc'

             r'|cc|c'

             r'|signext|zeroext|inreg|sret|nounwind|noreturn|noalias|nocapture'
             r'|byval|nest|readnone|readonly'
             r'|inlinehint|noinline|alwaysinline|optsize|ssp|sspreq|noredzone'
             r'|noimplicitfloat|naked'
             r'|builtin|cold|nobuiltin|noduplicate|nonlazybind|optnone'
             r'|returns_twice|sanitize_address|sanitize_memory|sanitize_thread'
             r'|sspstrong|uwtable|returned'

             r'|type|opaque'

             r'|eq|ne|slt|sgt|sle'
             r'|sge|ult|ugt|ule|uge'
             r'|oeq|one|olt|ogt|ole'
             r'|oge|ord|uno|ueq|une'
             r'|x'
             r'|acq_rel|acquire|alignstack|atomic|catch|cleanup|filter'
             r'|inteldialect|max|min|monotonic|nand|personality|release'
             r'|seq_cst|singlethread|umax|umin|unordered|xchg'

             # instructions
             r'|add|fadd|sub|fsub|mul|fmul|udiv|sdiv|fdiv|urem|srem|frem|shl'
             r'|lshr|ashr|and|or|xor|icmp|fcmp'

             r'|phi|call|trunc|zext|sext|fptrunc|fpext|uitofp|sitofp|fptoui'
             r'|fptosi|inttoptr|ptrtoint|bitcast|addrspacecast'
             r'|select|va_arg|ret|br|switch'
             r'|invoke|unwind|unreachable'
             r'|indirectbr|landingpad|resume'

             r'|malloc|alloca|free|load|store|getelementptr'

             r'|extractelement|insertelement|shufflevector|getresult'
             r'|extractvalue|insertvalue'

             r'|atomicrmw|cmpxchg|fence'

             r')\b', Keyword),

            # Types
            (r'void|half|float|double|x86_fp80|fp128|ppc_fp128|label|metadata',
             Keyword.Type),

            # Integer types
            (r'i[1-9]\d*', Keyword)
        ]
    }


class NasmLexer(RegexLexer):
    """
    For Nasm (Intel) assembly code.
    """
    name = 'NASM'
    aliases = ['nasm']
    filenames = ['*.asm', '*.ASM']
    mimetypes = ['text/x-nasm']

    identifier = r'[a-z$._?][\w$.?#@~]*'
    hexn = r'(?:0x[0-9a-f]+|$0[0-9a-f]*|[0-9]+[0-9a-f]*h)'
    octn = r'[0-7]+q'
    binn = r'[01]+b'
    decn = r'[0-9]+'
    floatn = decn + r'\.e?' + decn
    string = r'"(\\"|[^"\n])*"|' + r"'(\\'|[^'\n])*'|" + r"`(\\`|[^`\n])*`"
    declkw = r'(?:res|d)[bwdqt]|times'
    register = (r'r[0-9][0-5]?[bwd]|'
                r'[a-d][lh]|[er]?[a-d]x|[er]?[sb]p|[er]?[sd]i|[c-gs]s|st[0-7]|'
                r'mm[0-7]|cr[0-4]|dr[0-367]|tr[3-7]')
    wordop = r'seg|wrt|strict'
    type = r'byte|[dq]?word'
    directives = (r'BITS|USE16|USE32|SECTION|SEGMENT|ABSOLUTE|EXTERN|GLOBAL|'
                  r'ORG|ALIGN|STRUC|ENDSTRUC|COMMON|CPU|GROUP|UPPERCASE|IMPORT|'
                  r'EXPORT|LIBRARY|MODULE')

    flags = re.IGNORECASE | re.MULTILINE
    tokens = {
        'root': [
            (r'^\s*%', Comment.Preproc, 'preproc'),
            include('whitespace'),
            (identifier + ':', Name.Label),
            (r'(%s)(\s+)(equ)' % identifier,
                bygroups(Name.Constant, Keyword.Declaration, Keyword.Declaration),
                'instruction-args'),
            (directives, Keyword, 'instruction-args'),
            (declkw, Keyword.Declaration, 'instruction-args'),
            (identifier, Name.Function, 'instruction-args'),
            (r'[\r\n]+', Text)
        ],
        'instruction-args': [
            (string, String),
            (hexn, Number.Hex),
            (octn, Number.Oct),
            (binn, Number.Bin),
            (floatn, Number.Float),
            (decn, Number.Integer),
            include('punctuation'),
            (register, Name.Builtin),
            (identifier, Name.Variable),
            (r'[\r\n]+', Text, '#pop'),
            include('whitespace')
        ],
        'preproc': [
            (r'[^;\n]+', Comment.Preproc),
            (r';.*?\n', Comment.Single, '#pop'),
            (r'\n', Comment.Preproc, '#pop'),
        ],
        'whitespace': [
            (r'\n', Text),
            (r'[ \t]+', Text),
            (r';.*', Comment.Single)
        ],
        'punctuation': [
            (r'[,():\[\]]+', Punctuation),
            (r'[&|^<>+*/%~-]+', Operator),
            (r'[$]+', Keyword.Constant),
            (wordop, Operator.Word),
            (type, Keyword.Type)
        ],
    }


class NasmObjdumpLexer(ObjdumpLexer):
    """
    For the output of 'objdump -d -M intel'.

    .. versionadded:: 2.0
    """
    name = 'objdump-nasm'
    aliases = ['objdump-nasm']
    filenames = ['*.objdump-intel']
    mimetypes = ['text/x-nasm-objdump']

    tokens = _objdump_lexer_tokens(NasmLexer)


class Ca65Lexer(RegexLexer):
    """
    For ca65 assembler sources.

    .. versionadded:: 1.6
    """
    name = 'ca65 assembler'
    aliases = ['ca65']
    filenames = ['*.s']

    flags = re.IGNORECASE

    tokens = {
        'root': [
            (r';.*', Comment.Single),
            (r'\s+', Text),
            (r'[a-z_.@$][\w.@$]*:', Name.Label),
            (r'((ld|st)[axy]|(in|de)[cxy]|asl|lsr|ro[lr]|adc|sbc|cmp|cp[xy]'
             r'|cl[cvdi]|se[cdi]|jmp|jsr|bne|beq|bpl|bmi|bvc|bvs|bcc|bcs'
             r'|p[lh][ap]|rt[is]|brk|nop|ta[xy]|t[xy]a|txs|tsx|and|ora|eor'
             r'|bit)\b', Keyword),
            (r'\.\w+', Keyword.Pseudo),
            (r'[-+~*/^&|!<>=]', Operator),
            (r'"[^"\n]*.', String),
            (r"'[^'\n]*.", String.Char),
            (r'\$[0-9a-f]+|[0-9a-f]+h\b', Number.Hex),
            (r'\d+', Number.Integer),
            (r'%[01]+', Number.Bin),
            (r'[#,.:()=\[\]]', Punctuation),
            (r'[a-z_.@$][\w.@$]*', Name),
        ]
    }

    def analyse_text(self, text):
        # comments in GAS start with "#"
        if re.match(r'^\s*;', text, re.MULTILINE):
            return 0.9
