#!/bin/python
import io
import os


def find_files(target_dir, pattern):
    files = []
    for dirpath, dirnames, filenames in os.walk(target_dir):
        for f in filenames:
            if pattern(dirpath, f):
                files.append(os.path.join(dirpath, f))
    return files


def find_files_ext(target_dir, exts):
    if isinstance(exts, str):
        exts = [exts]

    def pattern(path, fname):
        basename, ext = os.path.splitext(fname)
        if ext in exts:
            return True
        else:
            return False

    return find_files(target_dir, pattern)


def filename_transform(f, prefix=("", ""), postfix=("", "")):
    prefix_from = prefix[0]
    prefix_to = prefix[1]
    postfix_from = postfix[0]
    postfix_to = postfix[1]
    if isinstance(f, str):
        prel = len(prefix_from)
        postl = len(postfix_from)
        s = 0
        e = len(f)
        if f.startswith(prefix_from):
            s += prel
        if f.endswith(postfix_from):
            e -= postl
        return prefix_to + f[s:e] + postfix_to
    else:
        return list(map(lambda x: filename_transform(x, prefix, postfix), f))


def listify(maybe_list):
    if isinstance(maybe_list, list):
        return maybe_list
    else:
        return [maybe_list]


def change_ext(f, ext):
    def ext(fname):
        b, e = os.path.splitext(fname)
        return f + ext

    if isinstance(f, str):
        return ext(f)
    else:
        return list(map(ext, f))


def list2str(li):
    if isinstance(li, str):
        return li + ' '
    with io.StringIO() as sio:
        for e in li:
            sio.write(e)
            sio.write(' ')
        return sio.getvalue()


class GenMake:
    def __init__(self, build_dir):
        self.build_dir = build_dir
        self.out = io.StringIO()
        self.file_targets = set()
        self.file_byprods = set()
        self.dir_targets = set()

    def include(self, files):
        self.out.write(f"include {list2str(files)}\n\n")

    def build_path(self, files, *, new_ext=None):
        def bpath(fname):
            if new_ext:
                b, e = os.path.splitext(fname)
                fname = b + new_ext
            return self.build_dir + "/" + fname

        if isinstance(files, str):
            return bpath(files)
        else:
            return list(map(bpath, files))

    def optional_include(self, files):
        self.out.write(f"-include {list2str(files)}\n\n")

    def __mkdir(self, obj_dir):
        if obj_dir in self.dir_targets:
            return
        self.dir_targets.add(obj_dir)

        self.out.write(f"{obj_dir}:\n")
        self.out.write(f"\tmkdir -p {obj_dir}\n\n")

    def __compile_cpp(self, obj, src, compile_flags, compiler):
        if obj in self.file_targets:
            return
        self.file_targets.add(obj)

        obj_dir = os.path.dirname(obj)
        self.out.write(f"{obj}: {src} | {obj_dir}\n")
        #MMD: only user header, no system header
        #MP: ignore non-exist headers
        self.out.write(
            f"\t{compiler} {compile_flags} -MMD -MP -c {src} -o {obj}\n\n")
        dep = filename_transform(obj, postfix=(".o", ".d"))
        self.optional_include(dep)
        self.file_byprods.add(dep)

        self.__mkdir(obj_dir)

    def __link_cpp(self, target, obj_files, link_flags, linker):
        if target in self.file_targets:
            return
        target_dir = os.path.dirname(target)
        self.out.write(f"{target}: {list2str(obj_files)} | {target_dir} \n")
        self.out.write(
            f"\t{linker} {list2str(obj_files)} {link_flags} -o {target}\n\n")
        self.file_targets.add(target)

        self.__mkdir(target_dir)

    def compile_cpp(self, src_files, compile_flags,
                    compiler="${cpp_compiler}"):
        src_files = listify(src_files)
        obj_files = self.build_path(src_files, new_ext=".o")
        for src, obj in zip(src_files, obj_files):
            self.__compile_cpp(obj, src, compile_flags, compiler)

        return obj_files

    def link_cpp(self, target, obj_files, link_flags, linker="${linker}"):
        target = self.build_path(target)
        self.__link_cpp(target, obj_files, link_flags, linker)
        return target

    def build_cpp(self,
                  target,
                  src_files,
                  compile_flags,
                  link_flags,
                  compiler="${cpp_compiler}",
                  linker="${linker}"):
        obj_files = self.compile_cpp(src_files, compile_flags, compiler)
        return self.link_cpp(target, obj_files, link_flags, linker), obj_files

    def aggregate(self, target, sources):
        sources = self.build_path(sources)
        self.out.write(f"{target}: {list2str(sources)}\n")
        self.out.write(f".PHONY: {target}\n\n")

    def clean(self, rmdir=True):
        self.out.write(f"clean:\n")
        self.out.write(f"\trm -f {list2str(self.file_targets)}\n")
        self.out.write(f"\trm -f {list2str(self.file_byprods)}\n")
        if rmdir:
            self.out.write(f"\trm -fd {list2str(self.dir_targets)}\n")
        self.out.write(f".PHONY: clean\n\n")

    def dump(self, filename="makefile"):
        with open(filename, 'w+') as f:
            f.write(self.out.getvalue())


cpp_compile_flags = "${compile_flags}"
cpp_link_flags = "${link_flags}"

g = GenMake("${build_dir}")
g.include("makefile.in")
g.aggregate("all", ["main", "utest"])

src = find_files_ext("src", ".cpp")
main, obj = g.build_cpp("main", src, cpp_compile_flags, cpp_link_flags)

gtest_src = "googletest/googletest/src/gtest-all.cc"
gtest_obj = g.compile_cpp(gtest_src, "${gtest_compile_flags}")

utest_src = find_files_ext("test", ".cpp")
utest_obj = g.compile_cpp(utest_src, "${utest_compile_flags}")

obj_nomain = list(filter(lambda f: os.path.basename(f) != "main.o", obj))
g.link_cpp("utest", gtest_obj + utest_obj + obj_nomain, "${utest_link_flags}")

g.clean()
g.dump()
