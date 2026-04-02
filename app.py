from flask import Flask, render_template, request, redirect, url_for, flash
import csv
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'budzets_2024'

CSV_FAILS = 'dati.csv'

# ── Datu ielāde no CSV ──────────────────────────────────────────────────────
def ielaadet_datus():
    dati = []
    if os.path.exists(CSV_FAILS):
        with open(CSV_FAILS, newline='', encoding='utf-8') as f:
            lasitajs = csv.DictReader(f)
            for rinda in lasitajs:
                rinda['summa'] = float(rinda['summa'])
                dati.append(rinda)
    return dati

# ── Datu saglabāšana CSV ────────────────────────────────────────────────────
def saglaabt_datus(dati):
    with open(CSV_FAILS, 'w', newline='', encoding='utf-8') as f:
        lauki = ['id', 'tips', 'summa', 'apraksts', 'datums']
        rakstitajs = csv.DictWriter(f, fieldnames=lauki)
        rakstitajs.writeheader()
        rakstitajs.writerows(dati)

# ── Galvenā lapa ────────────────────────────────────────────────────────────
@app.route('/')
def index():
    dati = ielaadet_datus()
    filtrs = request.args.get('filtrs', 'visi')

    if filtrs == 'ienakums':
        attелoti = [d for d in dati if d['tips'] == 'ienakums']
    elif filtrs == 'izdevums':
        attелoti = [d for d in dati if d['tips'] == 'izdevums']
    else:
        attелoti = dati

    ienakumi = sum(d['summa'] for d in dati if d['tips'] == 'ienakums')
    izdevumi = sum(d['summa'] for d in dati if d['tips'] == 'izdevums')
    bilance  = ienakumi - izdevumi

    return render_template('index.html',
                           dati=attелoti,
                           ienakumi=ienakumi,
                           izdevumi=izdevumi,
                           bilance=bilance,
                           filtrs=filtrs)

# ── Ieraksta pievienošana ───────────────────────────────────────────────────
@app.route('/pievienot', methods=['POST'])
def pievienot():
    tips    = request.form.get('tips', '').strip()
    apraksts = request.form.get('apraksts', '').strip()
    summa_str = request.form.get('summa', '').strip()

    # Validācija
    if not tips or not apraksts or not summa_str:
        flash('Lūdzu aizpildi visus laukus!', 'kļūda')
        return redirect('/')

    try:
        summa = float(summa_str.replace(',', '.'))
        if summa <= 0:
            raise ValueError
    except ValueError:
        flash('Summai jābūt pozitīvam skaitlim (piemēram: 25.50)!', 'kļūda')
        return redirect('/')

    dati = ielaadet_datus()
    jauns_id = max((int(d['id']) for d in dati), default=0) + 1

    dati.append({
        'id':       str(jauns_id),
        'tips':     tips,
        'summa':    summa,
        'apraksts': apraksts,
        'datums':   datetime.now().strftime('%d.%m.%Y %H:%M')
    })

    saglaabt_datus(dati)
    flash(f'Ieraksts "{apraksts}" veiksmīgi pievienots!', 'veiksme')
    return redirect('/')

# ── Ieraksta dzēšana ────────────────────────────────────────────────────────
@app.route('/dzest/<int:ieraksta_id>')
def dzest(ieraksta_id):
    dati = ielaadet_datus()
    dati = [d for d in dati if int(d['id']) != ieraksta_id]
    saglaabt_datus(dati)
    flash('Ieraksts izdzēsts.', 'info')
    return redirect('/')

# ── Bilances lapa ───────────────────────────────────────────────────────────
@app.route('/bilance')
def bilance():
    dati = ielaadet_datus()
    ienakumi = sum(d['summa'] for d in dati if d['tips'] == 'ienakums')
    izdevumi = sum(d['summa'] for d in dati if d['tips'] == 'izdevums')
    bilance  = ienakumi - izdevumi

    # Lielākie izdevumi
    izd_saraksts = sorted(
        [d for d in dati if d['tips'] == 'izdevums'],
        key=lambda x: x['summa'], reverse=True
    )[:5]

    return render_template('bilance.html',
                           ienakumi=ienakumi,
                           izdevumi=izdevumi,
                           bilance=bilance,
                           izd_saraksts=izd_saraksts,
                           kopskaits=len(dati))

if __name__ == '__main__':
    app.run(debug=True)
