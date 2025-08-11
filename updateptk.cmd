pushd .
cd ..\ptk
cmd/c build-cjs.cmd
popd
copy/y ..\ptk\nodebundle.cjs