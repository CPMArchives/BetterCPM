; PIP Build 027 RO approval read before shared-input migration.
; Source commit 6763f2a6dea8279668d42e593ee16b490b945539.
; Caller immediately compares Y.
        LD C,1
        CALL 5
        AND 0DFH
