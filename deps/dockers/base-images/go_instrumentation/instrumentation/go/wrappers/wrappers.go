package instrumentation

/*
	The command line must specify a library path (using CGO_LDFLAGS). CGO_CFLAGS
	need not be set, since the Antithesis instrumentation functions are declared
	inline, below. In the unlikely event that any of these changes, this file
	must also be changed. Inlining these declarations has proven to be less brittle
	than imposing a compile-time requirement on "instrumentation.h".

	Flags for CGO are collected, so the blank declarations have no effect.
	However, they can be modified in build scripts to be built into customer code.

	The C headers define the various integer types, as well as the free() function.
	See https://pkg.go.dev/cmd/cgo#hdr-Go_references_to_C for an explanation of all
	the type conversion below.

	Without these explicit dependencies on libraries, the Go compiler will link
	to a standard library of its choosing, resulting in SIGILL at run-time.
*/

// #cgo LDFLAGS: -lpthread -ldl -lc -lm -lvoidstar
// #cgo CFLAGS:
// #include <stdlib.h>
// #include <stdbool.h>
// int fuzz_getchar();
// void fuzz_info_message( const char* message );
// void fuzz_error_message( const char* message );
// size_t init_coverage_module(size_t edge_count, const char* symbol_file_name);
// bool notify_coverage(size_t edge_plus_module);
// void fuzz_exit(int exit_code);
import "C"

import (
	"fmt"
	"os"
	"unsafe"
)

// AntithesisGoInstrumentationVerbose points to the literal
// "ANT_GO_INSTRUMENTATION_VERBOSE". This environment variable
// should be present if you want every edge reported.
const AntithesisGoInstrumentationVerbose string = "ANT_GO_INSTRUMENTATION_VERBOSE"

var edgesVisited = map[uint32]bool{}
var moduleInitialized = false

// TODO What integer types would be best to use?
var moduleOffset uint64
var moduleEdgeCount = -1

// TODO Add an init() function to this package.
func getInstrumentationWrapperVerbose() bool {
	_, present := os.LookupEnv(AntithesisGoInstrumentationVerbose)
	return present
}

// InstrumentationWrapperVerbose reads environment variables specific
// to the Go instrumentation. Right now, this simply causes edge numbers
// to be written to stderr.
var instrumentationWrapperVerbose bool = getInstrumentationWrapperVerbose()

// InitializeModule should be called only once from a program.
func InitializeModule(symbolTable string, edgeCount int) uint64 {
	if moduleInitialized {
		// We cannot support incorrect workflows.
		panic("InitializeModule() has already been called!")
	}
	// WARN Re: integer type conversion, see https://github.com/golang/go/issues/29878
	executable, _ := os.Executable()
	InfoMessage(fmt.Sprintf("%s called antithesis.com/go/instrumentation.InitializeModule(%s, %d)", executable, symbolTable, edgeCount))
	s := C.CString(symbolTable)
	defer C.free(unsafe.Pointer(s))
	offset := C.init_coverage_module(C.ulong(edgeCount), s)
	moduleOffset = uint64(offset)
	moduleInitialized = true
	// TODO Determine if any custom code would ever want this; return void if not.
	return moduleOffset
}

// Notify will be called from instrumented code.
func Notify(edge int) bool {
	if !moduleInitialized {
		// We cannot support incorrect workflows.
		panic(fmt.Sprintf("antithesis.com/go/instrumentation.Notify() called before being initialized."))
	}
	edgePlusOffset := uint64(edge)
	edgePlusOffset += moduleOffset
	b := C.notify_coverage(C.ulong(edgePlusOffset))
	return bool(b)
}

// FuzzGetChar is for the use of the test harness.
func FuzzGetChar() byte {
	return (byte)(C.fuzz_getchar())
}

// FuzzExit is inserted by the instrumentation.
func FuzzExit(exit int) {
	C.fuzz_exit(C.int(exit))
}

// InfoMessage is for the use of the test harness.
func InfoMessage(message string) {
	s := C.CString(message)
	defer C.free(unsafe.Pointer(s))
	C.fuzz_info_message(s)
}

// ErrorMessage is for the use of the test harness.
func ErrorMessage(message string) {
	s := C.CString(message)
	defer C.free(unsafe.Pointer(s))
	C.fuzz_error_message(s)
}
