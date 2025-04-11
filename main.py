import logging from telegram import Update from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes from datetime import datetime

user_data = {}

logging.basicConfig( format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO )

def get_user_data(user_id): if user_id not in user_data: user_data[user_id] = { "mode": "pribadi", "pribadi": { "Dompet Utama": 0, "GoPay": 0, "Investasi": 0, "catatan": [] }, "bisnis": { "produk": {}, "transaksi": [] } } return user_data[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text( "Halo! Aku siap bantu catat keuanganmu.\nGunakan perintah:\n- /mode pribadi\n- /mode bisnis\n\nContoh: Masuk 100000 dari gaji" )

async def switch_mode(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.message.from_user.id args = context.args if not args or args[0] not in ["pribadi", "bisnis"]: await update.message.reply_text("Gunakan: /mode pribadi atau /mode bisnis") return user_data[user_id]["mode"] = args[0] await update.message.reply_text(f"Mode sekarang: {args[0].capitalize()}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.message.from_user.id text = update.message.text.lower() data = get_user_data(user_id)

if data["mode"] == "pribadi":
    pribadi = data["pribadi"]

    if text.startswith("masuk"):
        try:
            nominal = int(''.join(filter(str.isdigit, text.split()[1])))
            sumber = ' '.join(text.split()[3:]) or 'lainnya'
            pribadi["Dompet Utama"] += nominal
            pribadi["catatan"].append(("Masuk", nominal, sumber))
            await update.message.reply_text(f"Masuk Rp{nominal:,} dari {sumber}")
        except:
            await update.message.reply_text("Format tidak dikenali. Coba: Masuk 100000 dari gaji")

    elif text.startswith("keluar"):
        try:
            nominal = int(''.join(filter(str.isdigit, text.split()[1])))
            tujuan = ' '.join(text.split()[3:]) or 'lainnya'
            if pribadi["Dompet Utama"] >= nominal:
                pribadi["Dompet Utama"] -= nominal
                pribadi["catatan"].append(("Keluar", nominal, tujuan))
                await update.message.reply_text(f"Keluar Rp{nominal:,} untuk {tujuan}")
            else:
                await update.message.reply_text("Saldo tidak cukup.")
        except:
            await update.message.reply_text("Format salah. Coba: Keluar 50000 untuk makan")

    elif text.startswith("pindah"):
        try:
            nominal = int(text.split()[1])
            dari = text.split()[3].capitalize()
            ke = text.split()[5].capitalize()
            if dari in pribadi and ke in pribadi and pribadi[dari] >= nominal:
                pribadi[dari] -= nominal
                pribadi[ke] += nominal
                pribadi["catatan"].append(("Pindah", nominal, f"{dari} ke {ke}"))
                await update.message.reply_text(f"Pindah Rp{nominal:,} dari {dari} ke {ke}")
            else:
                await update.message.reply_text("Dompet tidak valid atau saldo tidak cukup")
        except:
            await update.message.reply_text("Format salah. Coba: Pindah 20000 dari Dompet Utama ke GoPay")

    elif "cek saldo" in text:
        await update.message.reply_text(
            f"Saldo saat ini:\nDompet Utama: Rp{pribadi['Dompet Utama']:,}\nGoPay: Rp{pribadi['GoPay']:,}\nInvestasi: Rp{pribadi['Investasi']:,}"
        )

    elif "reset catatan" in text:
        pribadi["catatan"] = []
        await update.message.reply_text("Catatan berhasil direset.")

    elif "catatan" in text:
        if not pribadi["catatan"]:
            await update.message.reply_text("Belum ada catatan transaksi.")
        else:
            lines = [f"{i+1}. {c[0]} Rp{c[1]:,} - {c[2]}" for i, c in enumerate(pribadi["catatan"][-10:])]
            await update.message.reply_text("Catatan terakhir:\n" + '\n'.join(lines))

    elif text.startswith("hapus catatan"):
        try:
            index = int(text.split()[-1]) - 1
            if 0 <= index < len(pribadi["catatan"]):
                hapus = pribadi["catatan"].pop(index)
                await update.message.reply_text(f"Catatan ke-{index+1} dihapus: {hapus}")
            else:
                await update.message.reply_text("Index tidak ditemukan")
        except:
            await update.message.reply_text("Format: Hapus catatan 2")

    elif text.startswith("edit catatan"):
        try:
            bagian = text.split()
            index = int(bagian[2]) - 1
            tipe = bagian[3].capitalize()
            jumlah = int(bagian[4])
            deskripsi = ' '.join(bagian[5:])
            if 0 <= index < len(pribadi["catatan"]):
                pribadi["catatan"][index] = (tipe, jumlah, deskripsi)
                await update.message.reply_text(f"Catatan ke-{index+1} diupdate")
            else:
                await update.message.reply_text("Index tidak valid")
        except:
            await update.message.reply_text("Format: Edit catatan 1 Masuk 200000 dari freelance")

    else:
        await update.message.reply_text("Perintah tidak dikenali dalam mode Pribadi.")

elif data["mode"] == "bisnis":
    bisnis = data["bisnis"]

    if text.startswith("produk"):
        try:
            _, nama, stok, harga_jual, harga_modal = text.split()
            bisnis["produk"][nama] = {
                "stok": int(stok),
                "jual": int(harga_jual),
                "modal": int(harga_modal)
            }
            await update.message.reply_text(f"Produk '{nama}' ditambahkan/diupdate.")
        except:
            await update.message.reply_text("Format salah. Coba: Produk sabun 10 15000 10000")

    elif text.startswith("jual"):
        try:
            _, nama, jumlah = text.split()
            jumlah = int(jumlah)
            if nama in bisnis["produk"] and bisnis["produk"][nama]["stok"] >= jumlah:
                produk = bisnis["produk"][nama]
                produk["stok"] -= jumlah
                total = produk["jual"] * jumlah
                profit = (produk["jual"] - produk["modal"]) * jumlah
                bisnis["transaksi"].append({
                    "tanggal": datetime.now().strftime("%Y-%m-%d"),
                    "produk": nama,
                    "jumlah": jumlah,
                    "total": total,
                    "profit": profit,
                    "tipe": "kas"
                })
                await update.message.reply_text(f"Transaksi berhasil. Total: Rp{total:,}, Profit: Rp{profit:,}")
            else:
                await update.message.reply_text("Stok tidak cukup atau produk tidak ditemukan.")
        except:
            await update.message.reply_text("Format salah. Coba: Jual sabun 2")

    elif "rekap" in text:
        bulan_ini = datetime.now().strftime("%Y-%m")
        total = sum(t["total"] for t in bisnis["transaksi"] if t["tanggal"].startswith(bulan_ini))
        await update.message.reply_text(f"Total transaksi bulan ini: Rp{total:,}")

    elif "profit" in text or "laba" in text:
        bulan_ini = datetime.now().strftime("%Y-%m")
        total_profit = sum(t.get("profit", 0) for t in bisnis["transaksi"] if t["tanggal"].startswith(bulan_ini))
        await update.message.reply_text(f"Total profit bulan ini: Rp{total_profit:,}")

    elif "stok" in text:
        if not bisnis["produk"]:
            await update.message.reply_text("Belum ada produk.")
        else:
            lines = [f"{p}: {d['stok']} pcs (Jual: Rp{d['jual']:,}, Modal: Rp{d['modal']:,})" for p, d in bisnis["produk"].items()]
            await update.message.reply_text("Stok saat ini:\n" + '\n'.join(lines))

    else:
        await update.message.reply_text("Perintah tidak dikenali dalam mode Bisnis.")

if name == 'main': from os import getenv import asyncio

TOKEN = "6105307352:AAHVp9tateOFRdP6-TSfvpv1oH66y564ciI"

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mode", switch_mode))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot jalan...")
    await app.run_polling()

asyncio.run(main())

