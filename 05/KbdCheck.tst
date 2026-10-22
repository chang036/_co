// Keyboard 路徑診斷用（不是正式測試，可以刪掉）
// 用法：在 Hardware Simulator 載入這個 script，看 KbdCheck.out 會一直長出 out 的值
//   按住大寫 K 時，某一行應該出現 out = 75
//   如果 out 永遠都是 0，代表「鍵盤事件沒進來」（GUI 問題），不是 Memory.hdl 的問題
//   注意：沒按 K 的話它會一直寫，用模擬器的 Stop 按鈕停掉

load Memory.hdl,
output-file KbdCheck.out,
output-list address%B1.15.1 out%D1.6.1;

set address 24576,

while out <> 75 {
    eval,
    output,
}
