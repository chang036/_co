// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq
@SP
M=M-1
A=M
D=M
@SP
M=M-1
A=M
D=M-D
@StackTest$eq_false.1
D;JNE
@SP
A=M
M=-1
@StackTest$eq_end.2
0;JMP
(StackTest$eq_false.1)
@SP
A=M
M=0
(StackTest$eq_end.2)

@SP
M=M+1
// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 16
@16
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq
@SP
M=M-1
A=M
D=M
@SP
M=M-1
A=M
D=M-D
@StackTest$eq_false.3
D;JNE
@SP
A=M
M=-1
@StackTest$eq_end.4
0;JMP
(StackTest$eq_false.3)
@SP
A=M
M=0
(StackTest$eq_end.4)

@SP
M=M+1
// push constant 16
@16
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq
@SP
M=M-1
A=M
D=M
@SP
M=M-1
A=M
D=M-D
@StackTest$eq_false.5
D;JNE
@SP
A=M
M=-1
@StackTest$eq_end.6
0;JMP
(StackTest$eq_false.5)
@SP
A=M
M=0
(StackTest$eq_end.6)

@SP
M=M+1
// push constant 892
@892
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@SP
M=M-1
A=M
D=M
@SP
M=M-1
A=M
D=M-D
@StackTest$lt_false.7
D;JGE
@SP
A=M
M=-1
@StackTest$lt_end.8
0;JMP
(StackTest$lt_false.7)
@SP
A=M
M=0
(StackTest$lt_end.8)

@SP
M=M+1
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 892
@892
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@SP
M=M-1
A=M
D=M
@SP
M=M-1
A=M
D=M-D
@StackTest$lt_false.9
D;JGE
@SP
A=M
M=-1
@StackTest$lt_end.10
0;JMP
(StackTest$lt_false.9)
@SP
A=M
M=0
(StackTest$lt_end.10)

@SP
M=M+1
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@SP
M=M-1
A=M
D=M
@SP
M=M-1
A=M
D=M-D
@StackTest$lt_false.11
D;JGE
@SP
A=M
M=-1
@StackTest$lt_end.12
0;JMP
(StackTest$lt_false.11)
@SP
A=M
M=0
(StackTest$lt_end.12)

@SP
M=M+1
// push constant 32767
@32767
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt
@SP
M=M-1
A=M
D=M
@SP
M=M-1
A=M
D=M-D
@StackTest$gt_false.13
D;JLE
@SP
A=M
M=-1
@StackTest$gt_end.14
0;JMP
(StackTest$gt_false.13)
@SP
A=M
M=0
(StackTest$gt_end.14)

@SP
M=M+1
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 32767
@32767
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt
@SP
M=M-1
A=M
D=M
@SP
M=M-1
A=M
D=M-D
@StackTest$gt_false.15
D;JLE
@SP
A=M
M=-1
@StackTest$gt_end.16
0;JMP
(StackTest$gt_false.15)
@SP
A=M
M=0
(StackTest$gt_end.16)

@SP
M=M+1
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt
@SP
M=M-1
A=M
D=M
@SP
M=M-1
A=M
D=M-D
@StackTest$gt_false.17
D;JLE
@SP
A=M
M=-1
@StackTest$gt_end.18
0;JMP
(StackTest$gt_false.17)
@SP
A=M
M=0
(StackTest$gt_end.18)

@SP
M=M+1
// push constant 57
@57
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 31
@31
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 53
@53
D=A
@SP
A=M
M=D
@SP
M=M+1
// add
@SP
M=M-1
A=M
D=M
@SP
A=M-1
M=D+M
// push constant 112
@112
D=A
@SP
A=M
M=D
@SP
M=M+1
// sub
@SP
M=M-1
A=M
D=M
@SP
A=M-1
M=M-D
// neg
@SP
A=M-1
M=-M
// and
@SP
M=M-1
A=M
D=M
@SP
A=M-1
M=D&M
// push constant 82
@82
D=A
@SP
A=M
M=D
@SP
M=M+1
// or
@SP
M=M-1
A=M
D=M
@SP
A=M-1
M=D|M
// not
@SP
A=M-1
M=!M

