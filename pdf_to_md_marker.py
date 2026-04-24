import os
import subprocess

def run_marker_batch():
    # 來源資料夾
    INPUT_FOLDER = "./my_pdfs"  
    # Marker 專屬的輸出資料夾
    OUTPUT_FOLDER = "./output_md_marker"  

    # 確保資料夾存在
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    print(f"準備將 {INPUT_FOLDER} 的 PDF 轉換至 {OUTPUT_FOLDER}...")
    print("注意：第一次執行會自動下載數 GB 的 AI 模型，請保持網路暢通！")

    # 【修正這裡】新版 Marker 必須使用 --output_dir 參數來指定輸出路徑
    command = ["marker", INPUT_FOLDER, "--output_dir", OUTPUT_FOLDER]
    
    try:
        # 呼叫 Marker 系統指令
        subprocess.run(command, check=True)
        print(f"\n✅ 轉換完成！請到 {OUTPUT_FOLDER} 查看結果。")
        print("每個 PDF 會產生一個獨立的資料夾，裡面包含 Markdown 與對應的圖片。")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 轉換過程發生錯誤: {e}")

if __name__ == "__main__":
    run_marker_batch()

