// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// Put your code here.
// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// 初始化 R2 = 0
@R2
M=0

// 載入 R1 到計數器 i (i = R1)
@R1
D=M
@i
M=D

(LOOP)
// 檢查計數器 i 是否 <= 0，若是則跳轉至 END
@i
D=M
@END
D;JLE

// 將 R0 的值累加到 R2 (R2 = R2 + R0)
@R0
D=M
@R2
M=M+D

// 計數器減 1 (i = i - 1)
@i
M=M-1

// 繼續下一輪迴圈
@LOOP
0;JMP

(END)
// 無窮迴圈，作為 Hack 程式的標準結尾
@END
0;JMP