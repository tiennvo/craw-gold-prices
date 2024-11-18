import requests
from bs4 import BeautifulSoup
import pymysql
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox
import json
from matplotlib import cm

host = "https://giavang.pnj.com.vn/"

def save_to_mysql(data):
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        db='gold',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with connection.cursor() as cursor:
            create_table_query = '''
                CREATE TABLE IF NOT EXISTS gold_prices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    area VARCHAR(100),
                    type VARCHAR(100),
                    buy VARCHAR(20),
                    sell VARCHAR(20),
                    date DATE
                )
            '''
            cursor.execute(create_table_query)
            
            insert_query = '''
                INSERT INTO gold_prices (area, type, buy, sell, date) VALUES (%s, %s, %s, %s, %s)
            '''
            cursor.executemany(insert_query, data)
        
        connection.commit()
        messagebox.showinfo("Thông báo", "Dữ liệu đã được lưu vào MySQL.")
        
    finally:
        connection.close()

def Craw():
    url = f"{host}"
    data = []
    rowspan_data = {}
    result = requests.get(url)

    if result.status_code == 200:
        soup = BeautifulSoup(result.content, 'html.parser')
        
        for row_index, row in enumerate(soup.find_all('tr')):
            columns = row.find_all('td')
            row_data = []

            col_index = 0

            while col_index < len(columns):

                cell = columns[col_index]
                rowspan = int(cell.get('rowspan', 1))

                row_data.append(cell.text.strip())

                if rowspan > 1:
                    for i in range(1, rowspan):
                        if row_index + i not in rowspan_data:
                            rowspan_data[row_index + i] = {}
                        rowspan_data[row_index + i][col_index] = cell.text.strip()

                col_index += 1

            if row_index in rowspan_data:
                for col, value in rowspan_data[row_index].items():
                    row_data.insert(col, value)

            if len(row_data) >= 4:
                today = datetime.now().strftime('%Y-%m-%d')
                data.append((*row_data[:4], today))
    print(data)
    save_to_mysql(data)

def fetch_gold_prices():
    from sqlalchemy import create_engine
    engine = create_engine('mysql+pymysql://root:@localhost/gold')
    query = """
    SELECT date, area, type, CAST(buy AS UNSIGNED) AS buy 
    FROM gold_prices 
    WHERE date IS NOT NULL
    ORDER BY date, area, type
    """
    df = pd.read_sql(query, engine)

    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
    df.dropna(subset=['date'], inplace=True) 
    return df


def plot_gold_prices_by_area(root):
    df = fetch_gold_prices()

    unique_combinations = df.groupby(['area', 'type']).size().index.tolist()
    #colors = cm.get_cmap('hsv', len(unique_combinations)).colors

    custom_colors = [
    '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#00FFFF', '#FF00FF',
    '#FF99FF', '#FF6666', '#663366', '#000000', '#006600', '#002200',
    '#000077', '#000044', '#330033', '#003366', '#FFFFCC', '#666633',
    '#FF6666', '#999999', '#A3FF33', '#999966', '#A333FF', '#33FFA8',
    '#99CCFF'
    ]
    fig, ax = plt.subplots(figsize=(12, 6))

    for i, (area, gold_type) in enumerate(unique_combinations):
        data = df[(df['area'] == area) & (df['type'] == gold_type)]
        ax.plot(
            data['date'],
            data['buy'],
            label=f"{area} - {gold_type}",
            color=custom_colors[i % len(custom_colors)],
            marker='o'
        )

    ax.set_title('Thống kê giá vàng theo khu vực và loại vàng')
    ax.set_xlabel('Ngày')
    ax.set_ylabel('Giá mua (VND)')
    ax.legend(title='Khu vực - Loại vàng', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)



def main():
    root = tk.Tk()
    root.title("Giá vàng")
    root.geometry("1200x800")

    btn_crawl = tk.Button(root, text="Cào dữ liệu", command=Craw, bg="lightblue")
    btn_crawl.pack(pady=10)


    btn_plot_area = tk.Button(root, text="Hiển thị biểu đồ giá vàng", 
                              command=lambda: plot_gold_prices_by_area(root), bg="lightcoral")
    btn_plot_area.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()
