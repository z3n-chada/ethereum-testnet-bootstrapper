package instrumentation

import (
	"sync"
	"math/rand"
	"testing"
)

const MaximumEdge = 50000;

func TestConcurrentGet(t *testing.T) {
	var b bitSet;
	var group sync.WaitGroup;

	for i := 0; i < MaximumEdge; i++ {
		group.Add(1)
		go func() {
			edge := int(rand.Int())
			b.Get(edge)
			group.Done()
		}()
	}

	group.Wait()
	if b.Size() != 0 {
		t.Errorf("Random Get() calls left a non-0 size: %d", b.Size())
	}
}

func TestConcurrentSet(t *testing.T) {
	var b bitSet;
	var group sync.WaitGroup;

	permuted := rand.Perm(MaximumEdge)

	for _, n := range(permuted) {
		group.Add(1)
		go func(edge int) {
			b.Set(edge)
			group.Done()
		}(n)
	}

	group.Wait()

	group.Wait()
	if b.Size() != MaximumEdge {
		t.Errorf("Concurrently setting all edges from 0..%d resulted in a size of %d", MaximumEdge, b.Size())
	}
}
