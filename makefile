include makefile.in 

all: ${build_dir}/test 
.PHONY: all

${build_dir}/src/main.o: src/main.cpp | ${build_dir}/src
	${cpp_compiler} ${compile_flags} -MMD -MP -c src/main.cpp -o ${build_dir}/src/main.o

-include ${build_dir}/src/main.d 

${build_dir}/src:
	mkdir -p ${build_dir}/src

${build_dir}/src/f.o: src/f.cpp | ${build_dir}/src
	${cpp_compiler} ${compile_flags} -MMD -MP -c src/f.cpp -o ${build_dir}/src/f.o

-include ${build_dir}/src/f.d 

${build_dir}/test: ${build_dir}/src/main.o ${build_dir}/src/f.o 
	${linker} ${build_dir}/src/main.o ${build_dir}/src/f.o  ${link_flags} -o ${build_dir}/test

clean:
	rm -f ${build_dir}/test ${build_dir}/src/f.o ${build_dir}/src/main.o 
	rm -f ${build_dir}/src/f.d ${build_dir}/src/main.d 
	rm -fd ${build_dir}/src 
.PHONY: clean

