package instrumentation

import (
	"testing"
)

func TestInfoMessage(t *testing.T) {
	InfoMessage("This is an informative message.")
}

func TestErrorMessage(t *testing.T) {
	ErrorMessage("This is an error message.")
}

func TestGetRandom(t *testing.T) {
	l := GetRandom()
	t.Logf("fuzz_get_random() returned 0x%x", l)
}