import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
import numpy as np
from astropy.io import fits
import pandas as pd
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class FitsProcessorApp:
    def __init__(self, master):
        self.master = master
        master.title("FITS Dosya İşleyici")

        self.label = tk.Label(master, text="Bir FITS dosyası seçin ve işleyin.")
        self.label.pack(pady=10)

        self.column_frame = tk.Frame(master)
        self.column_frame.pack(pady=5)

        self.label_col1 = tk.Label(self.column_frame, text="İlk Kolon İndeksi:")
        self.label_col1.grid(row=0, column=0, padx=5)

        self.entry_col1 = tk.Entry(self.column_frame, width=5)
        self.entry_col1.insert(0, "0")  # Varsayılan değer
        self.entry_col1.grid(row=0, column=1, padx=5)

        self.label_col2 = tk.Label(self.column_frame, text="İkinci Kolon İndeksi:")
        self.label_col2.grid(row=0, column=2, padx=5)

        self.entry_col2 = tk.Entry(self.column_frame, width=5)
        self.entry_col2.insert(0, "3")  # Varsayılan değer
        self.entry_col2.grid(row=0, column=3, padx=5)

        self.select_button = tk.Button(master, text="FITS Dosyası Seç ve İşle", command=self.process_fits_file)
        self.select_button.pack(pady=5)

        self.progress = ttk.Progressbar(master, orient='horizontal', mode='indeterminate')
        self.progress.pack(pady=5)

        self.status_label = tk.Label(master, text="")
        self.status_label.pack(pady=10)

        # Grafik çerçevesi
        self.plot_frame = tk.Frame(master)
        self.plot_frame.pack(pady=10)

    def process_fits_file(self):
        fits_file = filedialog.askopenfilename(
            title="İşlenecek .fits dosyasını seçin",
            filetypes=[("FITS Dosyaları", "*.fits"), ("Tüm Dosyalar", "*.*")]
        )

        if not fits_file:
            messagebox.showwarning("Uyarı", "Herhangi bir dosya seçilmedi.")
            return

        if not os.path.isfile(fits_file):
            messagebox.showerror("Hata", "Seçilen dosya bulunamadı.")
            return

        try:
            self.progress.start()
            self.status_label.config(text="İşlem devam ediyor...")

            hdul = fits.open(fits_file)
            data = hdul[1].data

            data_dict = {}
            for column in data.columns.names:
                flattened_data = np.concatenate(data[column])
                data_dict[column] = flattened_data

            df = pd.DataFrame(data_dict)
            try:
                col_index1 = int(self.entry_col1.get())
                col_index2 = int(self.entry_col2.get())
            except ValueError:
                messagebox.showerror("Hata", "Lütfen geçerli bir kolon indeksi girin.")
                self.progress.stop()
                self.status_label.config(text="İşlem başarısız oldu.")
                return

            max_col_index = len(df.columns) - 1

            if col_index1 < 0 or col_index1 > max_col_index or col_index2 < 0 or col_index2 > max_col_index:
                messagebox.showerror("Hata", f"Kolon indeksleri 0 ile {max_col_index} arasında olmalıdır.")
                self.progress.stop()
                self.status_label.config(text="İşlem başarısız oldu.")
                return

            selected_columns = df.iloc[:, [col_index1, col_index2]]

            filtered_data = selected_columns[selected_columns.iloc[:, 1] != 0]

            x_data = filtered_data.iloc[:, 0].values
            y_data = filtered_data.iloc[:, 1].values

            txt_output_file = os.path.splitext(fits_file)[0] + '_filtered.txt'
            np.savetxt(txt_output_file, np.column_stack((x_data, y_data)), fmt='%f', header='X_data Y_data')

            col1 = fits.Column(name='X_data', format='E', array=x_data)
            col2 = fits.Column(name='Y_data', format='E', array=y_data)
            cols = fits.ColDefs([col1, col2])

            hdu = fits.BinTableHDU.from_columns(cols)
            hdul_new = fits.HDUList([fits.PrimaryHDU(), hdu])

            output_fits_file = os.path.splitext(fits_file)[0] + '_filtered.fits'

            hdul_new.writeto(output_fits_file, overwrite=True)
            hdul.close()

            self.progress.stop()
            self.status_label.config(text="İşlem tamamlandı.")

            messagebox.showinfo(
                "Başarılı",
                f"İşlem tamamlandı.\n\n"
                f"Filtrelenmiş veriler '{txt_output_file}' dosyasına kaydedildi.\n"
                f"Yeni .fits dosyası: '{output_fits_file}'"
            )

            self.show_plot(x_data, y_data)

        except Exception as e:
            self.progress.stop()
            self.status_label.config(text="İşlem başarısız oldu.")
            messagebox.showerror("Hata", f"İşlem sırasında bir hata oluştu:\n{e}")

    def show_plot(self, x_data, y_data):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(x_data, y_data)
        ax.set_xlabel('Wavelenght')
        ax.set_ylabel('Flux')

        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = FitsProcessorApp(root)
    root.mainloop()