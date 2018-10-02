include makefile.in 

all: ${build_dir}/main ${build_dir}/utest 
.PHONY: all

${build_dir}/src/main.o: src/main.cpp | ${build_dir}/src
	${cpp_compiler} ${compile_flags} -MMD -MP -c src/main.cpp -o ${build_dir}/src/main.o

-include ${build_dir}/src/main.d 

${build_dir}/src:
	mkdir -p ${build_dir}/src

${build_dir}/src/f.o: src/f.cpp | ${build_dir}/src
	${cpp_compiler} ${compile_flags} -MMD -MP -c src/f.cpp -o ${build_dir}/src/f.o

-include ${build_dir}/src/f.d 

${build_dir}/main: ${build_dir}/src/main.o ${build_dir}/src/f.o  | ${build_dir} 
	${linker} ${build_dir}/src/main.o ${build_dir}/src/f.o  ${link_flags} -o ${build_dir}/main

${build_dir}:
	mkdir -p ${build_dir}

${build_dir}/googletest/googletest/src/gtest-all.o: googletest/googletest/src/gtest-all.cc | ${build_dir}/googletest/googletest/src
	${cpp_compiler} ${gtest_compile_flags} -MMD -MP -c googletest/googletest/src/gtest-all.cc -o ${build_dir}/googletest/googletest/src/gtest-all.o

-include ${build_dir}/googletest/googletest/src/gtest-all.d 

${build_dir}/googletest/googletest/src:
	mkdir -p ${build_dir}/googletest/googletest/src

${build_dir}/test/main.o: test/main.cpp | ${build_dir}/test
	${cpp_compiler} ${utest_compile_flags} -MMD -MP -c test/main.cpp -o ${build_dir}/test/main.o

-include ${build_dir}/test/main.d 

${build_dir}/test:
	mkdir -p ${build_dir}/test

${build_dir}/test/test.o: test/test.cpp | ${build_dir}/test
	${cpp_compiler} ${utest_compile_flags} -MMD -MP -c test/test.cpp -o ${build_dir}/test/test.o

-include ${build_dir}/test/test.d 

${build_dir}/utest: ${build_dir}/googletest/googletest/src/gtest-all.o ${build_dir}/test/main.o ${build_dir}/test/test.o ${build_dir}/src/f.o  | ${build_dir} 
	${linker} ${build_dir}/googletest/googletest/src/gtest-all.o ${build_dir}/test/main.o ${build_dir}/test/test.o ${build_dir}/src/f.o  ${utest_link_flags} -o ${build_dir}/utest

clean:
	rm -f ${build_dir}/main ${build_dir}/test/main.o ${build_dir}/utest ${build_dir}/test/test.o ${build_dir}/googletest/googletest/src/gtest-all.o ${build_dir}/src/main.o ${build_dir}/src/f.o 
	rm -f ${build_dir}/src/f.d ${build_dir}/test/main.d ${build_dir}/src/main.d ${build_dir}/test/test.d ${build_dir}/googletest/googletest/src/gtest-all.d 
	rm -fd ${build_dir} ${build_dir}/test ${build_dir}/googletest/googletest/src ${build_dir}/src 
.PHONY: clean

