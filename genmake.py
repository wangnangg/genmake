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

    def build_path(self, files):
        def bpath(fname):
            if os.path.dirname(fname) == '':
                return self.build_dir + "/" + fname
            else:
                return fname

        if isinstance(files, str):
            return bpath(files)
        else:
            return list(map(bpath, files))

    def optional_include(self, files):
        self.out.write(f"-include {list2str(files)}\n\n")

    def build_cpp(self,
                  target,
                  src_files,
                  compile_flags,
                  link_flags,
                  *,
                  compiler="${cpp_compiler}",
                  linker="${linker}",
                  cpp_ext=".cpp"):
        obj_files = filename_transform(
            src_files,
            prefix=("", self.build_dir + "/"),
            postfix=(cpp_ext, ".o"))
        for src, obj in zip(src_files, obj_files):
            if obj in self.file_targets:
                continue
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

            if obj_dir in self.dir_targets:
                continue
            self.dir_targets.add(obj_dir)

            self.out.write(f"{obj_dir}:\n")
            self.out.write(f"\tmkdir -p {obj_dir}\n\n")

        target = self.build_path(target)
        self.out.write(f"{target}: {list2str(obj_files)}\n")
        self.out.write(
            f"\t{linker} {list2str(obj_files)} {link_flags} -o {target}\n\n")
        self.file_targets.add(target)

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
g.aggregate("all", "test")

src_files = find_files_ext("src", ".cpp")
g.build_cpp("test", src_files, cpp_compile_flags, cpp_link_flags)
g.clean()
g.dump()
