from collections import OrderedDict
import os
import json

def ParseImportFile(fname):
    mod_dic = OrderedDict()
    with open(fname, 'r') as src:
        for line in src:
            if line in ['', '\n']:
                continue
            line = line.rstrip('\n')
            mod_name, lib_name, nid_str = line.split(' ')
            nid = int(nid_str, 16)

            if mod_name not in mod_dic:
                mod_dic[mod_name] = OrderedDict()

            lib_dic = mod_dic[mod_name]
            if lib_name not in lib_dic:
                lib_dic[lib_name] = []

            nid_list = lib_dic[lib_name]
            nid_list.append([nid, 'null'])

    return mod_dic


# some files in ps4libdoc stands for a library
# while most stands for a module
# so we have to fix this
def FixFileName(old_fname):
    new_fname = old_fname
    if new_fname == 'libSceAppContentUtil.sprx.json':
        new_fname = 'libSceAppContent.sprx.json'
    elif new_fname == 'libSceNpScore.sprx.json':
        new_fname = 'libSceNpScoreRanking.sprx.json'
    elif new_fname == 'libSceJson.sprx.json':
        new_fname = 'libSceJson2.sprx.json'

    return new_fname


# https://github.com/idc/ps4libdoc/tree/5.05
def GetFuncNameFromDB(db_root, imp_mods):
    for mod_name in imp_mods:

        print(f'process module {mod_name}')
        db_basename = f'{mod_name}.sprx.json'

        db_basename = FixFileName(db_basename)
        db_fname = os.path.join(db_root, db_basename)
        if not os.path.exists(db_fname):
            print(f'file not exist {db_fname}')
            exit(1)

        src = open(db_fname)
        db_obj = json.load(src)
        lib_dic = imp_mods[mod_name]
        db_mod_list = db_obj['modules']
        for db_mod_dic in db_mod_list:
            if db_mod_dic['name'] == mod_name:
                db_lib_list = db_mod_dic['libraries']
                break

        found_lib = False
        for lib_name in lib_dic:
            print(f'process library {lib_name}')
            for db_lib_dic in db_lib_list:
                if db_lib_dic['name'] == lib_name:
                    db_sym_list = db_lib_dic['symbols']
                    found_lib = True
                    break

            if not found_lib:
                print(f'can not find lib {lib_name} in {db_fname}')

            func_list = lib_dic[lib_name]


            for func_pair in func_list:
                for db_sym_dic in db_sym_list:
                    db_nid = db_sym_dic['id']
                    if db_nid == func_pair[0]:
                        db_sym_name = db_sym_dic['name']
                        func_name = db_sym_name or '_import_{:016X}'.format(func_pair[0])
                        func_pair[1] = func_name
                        break

def SortDic(imp_mods):

    def TakeFunc(elem):
        return elem[1]

    for mod_name in imp_mods:
        lib_dic = imp_mods[mod_name]
        for lib_name in lib_dic:
            func_list = lib_dic[lib_name]
            func_list.sort(key = TakeFunc)

def GetModFolderName(mod_name):
    return (
        f'Sce{mod_name.capitalize()}'
        if len(mod_name) < 6 or mod_name[:6] != 'libSce'
        else mod_name[3:]
    )


def GetCodeFileNames(mod_name):
    if len(mod_name) < 6 or mod_name[:6] != 'libSce':
        base_name = f'sce_{mod_name.lower()}'
    else:
        base_name = f'sce_{mod_name[6:].lower()}'

    return f'{base_name}.h', f'{base_name}.cpp', f'{base_name}_export.cpp'

def WriteHeadComment(dst, mod_name, lib_dic):
    dst.write('/*' + '\n')
    dst.write(' *' + '    ' + 'GPCS4' + '\n')
    dst.write(' *' + '    ' + '\n')
    dst.write(' *' + '    ' + 'This file implements:' + '\n')
    dst.write(' *' + '    ' + f'module: {mod_name}' + '\n')
    for lib_name in lib_dic:
        dst.write(' *' + '    ' + f'    library: {lib_name}' + '\n')
    dst.write(' *' + '    ' + '\n')
    dst.write(' */'+ '\n')

def WriteNote(dst):
    dst.write('// Note:' + '\n')
    dst.write(
        f'// The codebase is generated using {os.path.basename(__file__)}'
        + '\n'
    )
    dst.write('// ' + 'You may need to modify the code manually to fit development needs' + '\n')


def FuncNameByNid(nid):
    return '_import_{:016X}'.format(nid)

def WriteOneDecl(dst, func_name, nid):
    if not func_name:
        func_name = FuncNameByNid(nid)

    func_decl = f'int PS4API {func_name}(void);'
    dst.write(func_decl + '\n')
    dst.write('\n')

def WriteOneImpl(dst, func_name, nid):
    if not func_name:
        func_name = FuncNameByNid(nid)

    func_impl = f'int PS4API {func_name}(void)'
    dst.write(func_impl + '\n')
    dst.write('{' + '\n')
    dst.write('\tLOG_FIXME("Not implemented");' + '\n')
    dst.write('\treturn SCE_OK;' + '\n')
    dst.write('}' + '\n')
    dst.write('\n')

def WriteDeclaration(dst, func_list):
    for nid, func_name in func_list:
        WriteOneDecl(dst, func_name, nid)
        dst.write('\n')

def WriteDefination(dst, func_list):
    for nid, func_name in func_list:
        WriteOneImpl(dst, func_name, nid)
        dst.write('\n')


def GetExpModuleName(mod_name):
    fmt_mod_name = GetModFolderName(mod_name)
    return f'g_ExpModule{fmt_mod_name}'


# extern SCE_EXPORT_MODULE g_ExpModuleSceLibc;
def WriteExpTabExtern(dst, mod_name):
    var_name = GetExpModuleName(mod_name)
    dst.write(f'extern const SCE_EXPORT_MODULE {var_name};\n')

def GetFuncTableName(mod_name, lib_name):
    return f'g_p{mod_name}_{lib_name}_FunctionTable'

def WriteExpTabDefination(dst, mod_name, lib_dic):
    fmt_mod_name = GetModFolderName(mod_name)
    for lib_name in lib_dic:
        func_tab_name = GetFuncTableName(fmt_mod_name, lib_name)
        lib_def_line = f'static const SCE_EXPORT_FUNCTION {func_tab_name}[] =\n'

        dst.write(lib_def_line)
        dst.write('{\n')

        func_list = lib_dic[lib_name]
        for nid, func in func_list:
            func_ent_line = '\t{{ 0x{0:016X}, "{1:}", (void*){1:} }},\n'.format(nid, func)
            dst.write(func_ent_line)

        dst.write('\tSCE_FUNCTION_ENTRY_END\n')
        dst.write('};\n')
        dst.write('\n')


    lib_ent_name = f'g_p{fmt_mod_name}_LibTable'
    lib_ent_def = f'static const SCE_EXPORT_LIBRARY {lib_ent_name}[] =\n'
    dst.write(lib_ent_def)
    dst.write('{\n')

    for lib_name in lib_dic:
        func_tab_name = GetFuncTableName(fmt_mod_name, lib_name)
        lib_ent_line = '\t{{ "{}", {} }},\n'.format(lib_name, func_tab_name)
        dst.write(lib_ent_line)

    dst.write('\tSCE_LIBRARY_ENTRY_END\n')
    dst.write('};\n')
    dst.write('\n')

    mod_def_name = GetExpModuleName(mod_name)
    mod_def_line = f'const SCE_EXPORT_MODULE {mod_def_name} =\n'
    dst.write(mod_def_line)
    dst.write('{\n')
    dst.write(f'\t"{mod_name}",\n')
    dst.write(f'\t{lib_ent_name}\n')
    dst.write('};\n')
    dst.write('\n\n')


def WriteInclude(dst, h_name):
    dst.write(f'#include "{h_name}"' + '\n')

def WritePragmaOnce(dst):
    dst.write('#pragma once' + '\n')

def WriteLibComment(dst, lib_name):
    dst.write('//////////////////////////////////////////////////////////////////////////' + '\n')
    dst.write(f'// library: {lib_name}' + '\n')
    dst.write('//////////////////////////////////////////////////////////////////////////' + '\n')


def WriteModuleFuncDecl(dst):
    dst.write('bool module_start(void* ctx);\n')
    dst.write('void module_exit(void);\n')


def WriteModuleFuncImpl(dst):
    dst.write('bool module_start(void* ctx)\n')
    dst.write('{\n')
    dst.write('\treturn true;\n')
    dst.write('}\n')
    dst.write('\n\n')

    dst.write('void module_exit(void)\n')
    dst.write('{\n')
    dst.write('}\n')


def WriteSourceFiles(fname_h, fname_cpp, fname_exp, mod_name, lib_dic):
    with (open(fname_h, 'w') as dst_h, open(fname_cpp, 'w') as dst_cpp, open(fname_exp, 'w') as dst_exp):

        print(
            f'write source file {os.path.basename(fname_h)} {os.path.basename(fname_cpp)} {os.path.basename(fname_exp)}'
        )

        WriteHeadComment(dst_h, mod_name, lib_dic)
        dst_h.write('\n')
        WritePragmaOnce(dst_h)
        dst_h.write('\n')
        WriteInclude(dst_h, 'sce_module_common.h')
        dst_h.write('\n\n')
        WriteExpTabExtern(dst_h, mod_name)
        dst_h.write('\n\n')
        # WriteModuleFuncDecl(dst_h)
        # dst_h.write('\n\n')
        WriteNote(dst_h)
        dst_h.write('\n\n\n')

        WriteInclude(dst_cpp, os.path.basename(fname_h))
        dst_cpp.write('\n\n')
        WriteNote(dst_cpp)
        dst_cpp.write('\n\n\n')

        for lib_name in lib_dic:
            func_list = lib_dic[lib_name]

            WriteLibComment(dst_h, lib_name)
            dst_h.write('\n')
            WriteDeclaration(dst_h, func_list)
            dst_h.write('\n\n')

            WriteLibComment(dst_cpp, lib_name)
            dst_cpp.write('\n')
            WriteDefination(dst_cpp, func_list)
            dst_cpp.write('\n\n')

        # WriteModuleFuncImpl(dst_cpp)

        WriteInclude(dst_exp, os.path.basename(fname_h))
        dst_exp.write('\n\n')
        WriteNote(dst_exp)
        dst_exp.write('\n\n')
        WriteExpTabDefination(dst_exp, mod_name, lib_dic)




def WriteCodeFile(root_dir, imp_mods):

    if not os.path.exists(root_dir):
        os.mkdir(root_dir)

    for mod_name in imp_mods:
        mod_folder = GetModFolderName(mod_name)
        mod_folder = os.path.join(root_dir, mod_folder)
        if not os.path.exists(mod_folder):
            os.mkdir(mod_folder)

        mod_h, mod_cpp, mod_exp_cpp = GetCodeFileNames(mod_name)
        fname_h = os.path.join(mod_folder, mod_h)
        fname_cpp = os.path.join(mod_folder, mod_cpp)
        fname_exp = os.path.join(mod_folder, mod_exp_cpp)

        lib_dic = imp_mods[mod_name]
        WriteSourceFiles(fname_h, fname_cpp, fname_exp, mod_name, lib_dic)


def Main():
    # this file is generated by eboot import table, from VS log ouput
    imp_mods = ParseImportFile('import_modules.txt')
    GetFuncNameFromDB('system\\common\\lib', imp_mods)
    SortDic(imp_mods)
    WriteCodeFile('SceModules', imp_mods)
    print('done!')

if __name__ == '__main__':
    Main()