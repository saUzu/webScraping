from bs4 import BeautifulSoup as bs
from requests_html import HTMLSession
import sqlite3
import datetime
import numpy as np
from sqlite3 import Error
import matplotlib.pyplot as ciz
import matplotlib.dates as mdates
import wx
import re
import os
from fuzzywuzzy import fuzz

cmSayfa = '?sayfa='
migrosSiviYag = 'https://www.migros.com.tr/sivi-yag-c-76'
migrosGaz = 'https://www.migros.com.tr/gazli-icecek-c-80'
migrosPeynir = 'https://www.migros.com.tr/peynir-c-6d'
migrosMakarna = 'https://www.migros.com.tr/makarna-c-425'

aSayfa = '?page='

aSiviYag = 'https://www.a101.com.tr/market/sivi-yag/'
aGaz = 'https://www.a101.com.tr/market/kola-gazoz-enerji-icecegi/'
aPeynir = 'https://www.a101.com.tr/market/peynir/'
aMakarna = 'https://www.a101.com.tr/market/makarna/'

cagriSiviYag = 'https://www.cagri.com/sivi-yaglar'
cagriGaz = 'https://www.cagri.com/gazli-icecekler'
cagriPeynir = 'https://www.cagri.com/peynirler'
cagriMakarna = 'https://www.cagri.com/makarna-eriste'

migrosUrunler = []
aUrunler = []
cagriUrunler = []

cekilenOrtakUrunler = []
urunlerinSiraSayisi = []

###################---VERİ TABANI İŞLEMLERİ---###################
def veriTabaninaBaglan():
    vtDosyasi = os.path.abspath(os.getcwd())+r'\vt\stajProjesi.db'
    try:
        baglanti = sqlite3.connect(vtDosyasi)
    except Error as hata:
        wx.MessageDialog(None, 'Veri tabanına bağlanılamadı', 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
        return None
        #print('Veri tabanına bağlanamadı. Hata: '+str(hata))
    else:
        #print(sqlite3.version)
        return baglanti

def veriTabaniTablo(baglanti):
    yagBilgiTablo = '''create table IF NOT EXISTS yagUrunleriT(
                                urunSira integer primary key asc,
                                yagAd text not null,
                                yagDigerAd text null,
                                yagTipi text not null,
                                yagAgirlik not null
                    );'''
    yagFiyatTablo = '''create table IF NOT EXISTS yagFiyatT(
                                fiyatSira integer primary key asc,
                                tarih text not null,
                                migFiyat text null,
                                aFiyat text null,
                                caFiyat text null,
                                urunSira integer not null,
                                foreign key(urunSira) references yagUrunleriT(urunSira)
                    );'''
    
    icecekBilgiTablo = '''create table IF NOT EXISTS icecekUrunleriT(
                                urunSira integer primary key asc,
                                icecekAd text not null,
                                icecekDigerAd text null,
                                icecekAgirlik not null
                            );'''
    icecekFiyatTablo = '''create table IF NOT EXISTS icecekFiyatT(
                                fiyatSira integer primary key asc,
                                tarih text not null,
                                migFiyat text null,
                                aFiyat text null,
                                caFiyat text null,
                                urunSira integer not null,
                                foreign key(urunSira) references icecekUrunleriT(urunSira)
                            );'''
    
    peynirBilgiTablo = '''create table IF NOT EXISTS peynirUrunleriT(
                                urunSira integer primary key asc,
                                peynirAd text not null,
                                peynirDigerAd text null,
                                peynirAgirlik not null
                            );'''
    peynirFiyatTablo = '''create table IF NOT EXISTS peynirFiyatT(
                                fiyatSira integer primary key asc,
                                tarih text not null,
                                migFiyat text null,
                                aFiyat text null,
                                caFiyat text null,
                                urunSira integer not null,
                                foreign key(urunSira) references peynirUrunleriT(urunSira)
                            );'''

    makarnaBilgiTablo = '''create table IF NOT EXISTS makarnaUrunleriT(
                                urunSira integer primary key asc,
                                makarnaAd text not null,
                                makarnaDigerAd text null,
                                makarnaAgirlik not null
                            );'''
    makarnaFiyatTablo = '''create table IF NOT EXISTS makarnaFiyatT(
                                fiyatSira integer primary key asc,
                                tarih text not null,
                                migFiyat text null,
                                aFiyat text null,
                                caFiyat text null,
                                urunSira integer not null,
                                foreign key(urunSira) references makarnaUrunleriT(urunSira)
                            );'''



    try:
        imlec = baglanti.cursor()
    except Error as hata:
        print('İmleç oluşturulamadı. Hata: '+str(hata))
    else:
        try:
            imlec.execute(yagBilgiTablo)
            imlec.execute(icecekBilgiTablo)
            imlec.execute(peynirBilgiTablo)
            imlec.execute(makarnaBilgiTablo)
        except Error as hata:
            wx.MessageDialog(None, 'Ürün bilgileri için tablo oluşturulamadı. \nHata: '+str(hata), 'HATA', wx.OK | wx.ICON_ERROR).ShowModal()
            return 0
        else:
            baglanti.commit()
            try:
                imlec.execute(yagFiyatTablo)
                imlec.execute(icecekFiyatTablo)
                imlec.execute(peynirFiyatTablo)
                imlec.execute(makarnaFiyatTablo)
            except Error as hata:
                wx.MessageDialog(None, 'Ürün fiyatları için tablo oluşturulamadı. \nHata: '+str(hata), 'HATA', wx.OK | wx.ICON_ERROR).ShowModal()
                return 0
            else:
                baglanti.commit()
                wx.MessageDialog(None, 'Tablolar oluşturuldu.', 'OLDU', wx.OK | wx.ICON_INFORMATION).ShowModal()
                return 1

def verileriTabloyaEkle(baglanti, secilen):
    urunBilgiE = '''insert into yagUrunleriT(yagAd,yagDigerAd,yagTipi,yagAgirlik) values(?,?,?,?)'''
    urunFiyatE = '''insert into yagFiyatT(tarih,migFiyat,aFiyat,caFiyat,urunSira) values(?,?,?,?,?)'''
    aramaKomutu = '''select urunSira from yagUrunleriT where yagAd=? and yagDigerAd=? and yagTipi=? and yagAgirlik=?'''

    icecekBilgiE = '''insert into icecekUrunleriT(icecekAd,icecekDigerAd,icecekAgirlik) values(?,?,?)'''
    icecekFiyatE = '''insert into icecekFiyatT(tarih,migFiyat,aFiyat,caFiyat,urunSira) values(?,?,?,?,?)'''
    icecekAramaK = '''select urunSira from icecekUrunleriT where icecekAd=? and icecekDigerAd=? and icecekAgirlik=?'''

    peynirBilgiE = '''insert into peynirUrunleriT(peynirAd,peynirDigerAd,peynirAgirlik) values(?,?,?)'''
    peynirFiyatE = '''insert into peynirFiyatT(tarih,migFiyat,aFiyat,caFiyat,urunSira) values(?,?,?,?,?)'''
    peynirAramaK = '''select urunSira from peynirUrunleriT where peynirAd=? and peynirDigerAd=? and peynirAgirlik=?'''

    makarnaBilgiE = '''insert into makarnaUrunleriT(makarnaAd,makarnaDigerAd,makarnaAgirlik) values(?,?,?)'''
    makarnaFiyatE = '''insert into makarnaFiyatT(tarih,migFiyat,aFiyat,caFiyat,urunSira) values(?,?,?,?,?)'''
    makarnaAramaK = '''select urunSira from makarnaUrunleriT where makarnaAd=? and makarnaDigerAd=? and makarnaAgirlik=?'''


    

    if secilen == 0:
        try:
            imlec = baglanti.cursor()
        except Error as hata:
            wx.MessageDialog(None, 'İmleç oluşturmada hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
            return 0
        else:
            for urun in cekilenOrtakUrunler:
                try:
                    imlec.execute(aramaKomutu, (urun[0], urun[1], urun[2], urun[3]))
                except Error as hata:
                    wx.MessageDialog(None, 'İsme göre ürün sırası arama hatası(Bilgi için).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    return 0
                else:
                    sira = imlec.fetchone()
                    if sira is None:
                        try:
                            imlec.execute(urunBilgiE, (urun[0], urun[1], urun[2], urun[3]))
                        except Error as hata:
                            wx.MessageDialog(None, 'Ürün bilgi eklemede hata.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                            return 0
                        else:
                            baglanti.commit()

            for urun in cekilenOrtakUrunler:
                try:
                    imlec.execute(aramaKomutu, (urun[0], urun[1], urun[2], urun[3]))
                except Error as hata:
                    wx.MessageDialog(None, 'İsme göre ürün sırası arama hatası(Fiyat için).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    return 0
                else:
                    sira = imlec.fetchone()
                    if sira is not None:
                        try:
                            tarih = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                            imlec.execute(urunFiyatE, (tarih, urun[4], urun[5], urun[6], sira[0]))
                        except Error as hata:
                            wx.MessageDialog(None, 'Ürün fiyat eklemede hata.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                            return 0
                        else:
                            baglanti.commit()
        return 1
    elif secilen == 1:
        try:
            imlec = baglanti.cursor()
        except Error as hata:
            wx.MessageDialog(None, 'İmleç oluşturmada hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
            return 0
        else:
            for urun in cekilenOrtakUrunler:
                try:
                    if urun[0][0] != '-':
                        imlec.execute(icecekAramaK, (urun[0][0], urun[0][1], urun[0][2]))
                    elif urun[1][0] != '-':
                        imlec.execute(icecekAramaK, (urun[1][0], urun[1][1], urun[1][2]))
                    elif urun[2][0] != '-':
                        imlec.execute(icecekAramaK, (urun[2][0], urun[2][1], urun[2][2]))
                except Error as hata:
                    wx.MessageDialog(None, 'İsme göre ürün sırası arama hatası(Bilgi için).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    return 0
                else:
                    sira = imlec.fetchone()
                    if sira is None:
                        try:
                            if urun[0][0] != '-':
                                imlec.execute(icecekBilgiE, (urun[0][0], urun[0][1], urun[0][2]))
                            elif urun[1][0] != '-':
                                imlec.execute(icecekBilgiE, (urun[1][0], urun[1][1], urun[1][2]))
                            elif urun[2][0] != '-':
                                imlec.execute(icecekBilgiE, (urun[2][0], urun[2][1], urun[2][2]))
                        except Error as hata:
                            wx.MessageDialog(None, 'Ürün bilgi eklemede hata.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                            return 0
                        else:
                            baglanti.commit()
            for urun in cekilenOrtakUrunler:
                try:
                    if urun[0][0] != '-':
                        imlec.execute(icecekAramaK, (urun[0][0], urun[0][1], urun[0][2]))
                    elif urun[1][0] != '-':
                        imlec.execute(icecekAramaK, (urun[1][0], urun[1][1], urun[1][2]))
                    elif urun[2][0] != '-':
                        imlec.execute(icecekAramaK, (urun[2][0], urun[2][1], urun[2][2]))
                except Error as hata:
                    wx.MessageDialog(None, 'İsme göre ürün sırası arama hatası(Fiyat için).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    return 0
                else:
                    sira = imlec.fetchone()
                    if sira is not None:
                        try:
                            tarih = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                            imlec.execute(icecekFiyatE, (tarih, urun[0][3], urun[1][3], urun[2][3], sira[0]))
                        except Error as hata:
                            wx.MessageDialog(None, 'Ürün fiyat eklemede hata.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                            return 0
                        else:
                            baglanti.commit()
        return 1
    elif secilen == 2:
        try:
            imlec = baglanti.cursor()
        except Error as hata:
            wx.MessageDialog(None, 'İmleç oluşturmada hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
            return 0
        else:
            for urun in cekilenOrtakUrunler:
                try:
                    if urun[0][0] != '-':
                        imlec.execute(peynirAramaK, (urun[0][0], urun[0][1], urun[0][2]))
                    elif urun[1][0] != '-':
                        imlec.execute(peynirAramaK, (urun[1][0], urun[1][1], urun[1][2]))
                    elif urun[2][0] != '-':
                        imlec.execute(peynirAramaK, (urun[2][0], urun[2][1], urun[2][2]))
                except Error as hata:
                    wx.MessageDialog(None, 'İsme göre ürün sırası arama hatası(Bilgi için).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    return 0
                else:
                    sira = imlec.fetchone()
                    if sira is None:
                        try:
                            if urun[0][0] != '-':
                                imlec.execute(peynirBilgiE, (urun[0][0], urun[0][1], urun[0][2]))
                            elif urun[1][0] != '-':
                                imlec.execute(peynirBilgiE, (urun[1][0], urun[1][1], urun[1][2]))
                            elif urun[2][0] != '-':
                                imlec.execute(peynirBilgiE, (urun[2][0], urun[2][1], urun[2][2]))
                        except Error as hata:
                            wx.MessageDialog(None, 'Ürün bilgi eklemede hata.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                            return 0
                        else:
                            baglanti.commit()

            for urun in cekilenOrtakUrunler:
                try:
                    if urun[0][0] != '-':
                        imlec.execute(peynirAramaK, (urun[0][0], urun[0][1], urun[0][2]))
                    elif urun[1][0] != '-':
                        imlec.execute(peynirAramaK, (urun[1][0], urun[1][1], urun[1][2]))
                    elif urun[2][0] != '-':
                        imlec.execute(peynirAramaK, (urun[2][0], urun[2][1], urun[2][2]))
                except Error as hata:
                    wx.MessageDialog(None, 'İsme göre ürün sırası arama hatası(Fiyat için).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    return 0
                else:
                    sira = imlec.fetchone()
                    if sira is not None:
                        try:
                            tarih = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                            imlec.execute(peynirFiyatE, (tarih, urun[0][3], urun[1][3], urun[2][3], sira[0]))
                        except Error as hata:
                            wx.MessageDialog(None, 'Ürün fiyat eklemede hata.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                            return 0
                        else:
                            baglanti.commit()
        return 1
    elif secilen == 3:
        try:
            imlec = baglanti.cursor()
        except Error as hata:
            wx.MessageDialog(None, 'İmleç oluşturmada hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
            return 0
        else:
            for urun in cekilenOrtakUrunler:
                try:
                    if urun[0][0] != '-':
                        imlec.execute(makarnaAramaK, (urun[0][0], urun[0][1], urun[0][2]))
                    elif urun[1][0] != '-':
                        imlec.execute(makarnaAramaK, (urun[1][0], urun[1][1], urun[1][2]))
                    elif urun[2][0] != '-':
                        imlec.execute(makarnaAramaK, (urun[2][0], urun[2][1], urun[2][2]))
                except Error as hata:
                    wx.MessageDialog(None, 'İsme göre ürün sırası arama hatası(Bilgi için).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    return 0
                else:
                    sira = imlec.fetchone()
                    if sira is None:
                        try:
                            if urun[0][0] != '-':
                                imlec.execute(makarnaBilgiE, (urun[0][0], urun[0][1], urun[0][2]))
                            elif urun[1][0] != '-':
                                imlec.execute(makarnaBilgiE, (urun[1][0], urun[1][1], urun[1][2]))
                            elif urun[2][0] != '-':
                                imlec.execute(makarnaBilgiE, (urun[2][0], urun[2][1], urun[2][2]))
                        except Error as hata:
                            wx.MessageDialog(None, 'Ürün bilgi eklemede hata.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                            return 0
                        else:
                            baglanti.commit()

            for urun in cekilenOrtakUrunler:
                try:
                    if urun[0][0] != '-':
                        imlec.execute(makarnaAramaK, (urun[0][0], urun[0][1], urun[0][2]))
                    elif urun[1][0] != '-':
                        imlec.execute(makarnaAramaK, (urun[1][0], urun[1][1], urun[1][2]))
                    elif urun[2][0] != '-':
                        imlec.execute(makarnaAramaK, (urun[2][0], urun[2][1], urun[2][2]))
                    
                except Error as hata:
                    wx.MessageDialog(None, 'İsme göre ürün sırası arama hatası(Fiyat için).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    return 0
                else:
                    sira = imlec.fetchone()
                    if sira is not None:
                        try:
                            tarih = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                            imlec.execute(makarnaFiyatE, (tarih, urun[0][3], urun[1][3], urun[2][3], sira[0]))
                        except Error as hata:
                            wx.MessageDialog(None, 'Ürün fiyat eklemede hata.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                            return 0
                        else:
                            baglanti.commit()
        return 1
#################################################################
###################---İNTERNETTEN ÜRÜN ÇEKME İŞLEMLERİ---###################
def arama(kelime, aranacakListe):
    gecici = ''
    for aranacak in aranacakListe:
        if kelime == aranacak:
            gecici = kelime
            return gecici
    return ''

def siviYagIsimEleme(ayrilmis):
    gecici = []
    urunMarkalari = ['KOMILI', 'YUDUM', 'KIRLANGIÇ', 'TARIŞ', 'ORKIDE', 'ZADE', 'KRISTAL', 'SIRMA']
    yagTipi = ['AYÇIÇEK', 'ZEYTINYAĞI', 'ZEYTINYAĞ', 'BITKISEL', 'MISIR', 'MISIRÖZÜ']
    yagBelirteci = ['SIZMA', 'RIVIERA', 'AKDENIZ', 'LEZZETLERI', 'KUZEY', 'EGE', 'EGEMDEN', 'ZIYAFET', 'GÜNEY', 'EGE', 'KIZARTMA' ,'YUMUŞAK', 'YOĞUN', 'YALIN', 'AYDIN', 'MILAS', 'AYVALIK', 'BIRINCI', 'SOĞUK', 'SIKMA', '1915', 'ERKENCE', 'KIDONIA']
    zadeAyrac = ['NAR', 'FESLEĞEN', 'LIMON', 'SARIMSAK', 'BIBERIYE', 'DEFNE', 'PORTAKAL', 'KIMYON', 'KIRMIZI', 'BIBER', 'KARABIBER']
    agirlikSayi = ['1', '2', '3', '4', '5', '1.25', '250', '4.5', '4,5', '300', '750', '500', '400', '1000', '1/2', '250ML','3000']

    #print(ayrilmis)
    yaginMarkasi = ''
    yaginAgirligi = ''
    yaginTuru = ''
    yaginGerisi = ''
    for kelime in ayrilmis:
        bulunan = arama(ayrilmis[0], urunMarkalari)
        if bulunan != '':
            bulunan = arama(kelime, urunMarkalari)
            if bulunan != '':
                yaginMarkasi = bulunan
            else:
                bulunan = arama(kelime, yagTipi)
                if bulunan != '':
                    if bulunan == 'ZEYTINYAĞ':
                        bulunan = 'ZEYTINYAĞI'
                    elif bulunan == 'MISIR':
                        bulunan = 'MISIRÖZÜ'
                    yaginTuru = bulunan
                else:
                    bulunan = arama(kelime, yagBelirteci)
                    if bulunan != '':
                        if bulunan == 'YALIN':
                            bulunan = 'YUMUŞAK'
                        yaginGerisi = yaginGerisi + ' ' + bulunan
                    else:
                        bulunan = arama(kelime, zadeAyrac)
                        if bulunan != '':
                            yaginGerisi = yaginGerisi + ' ' + bulunan
                        else:
                            bulunan = arama(kelime, agirlikSayi)
                            if bulunan != '':
                                if bulunan == '1000':
                                    bulunan = '1'
                                elif bulunan =='1/2':
                                    bulunan = '500'
                                elif bulunan == '250ML':
                                    bulunan ='250'
                                elif bulunan == '3000':
                                    bulunan = '3'
                                elif bulunan =='4,5':
                                    bulunan = '4.5'
                                yaginAgirligi = bulunan
    if yaginMarkasi=='ZADE' and not('SIZMA' in yaginGerisi):
        yaginGerisi = yaginGerisi + ' SIZMA'
        yaginGerisi.strip()

    gecici.extend([yaginMarkasi, yaginGerisi.strip(), yaginTuru, yaginAgirligi])
    return gecici

def icecekIsimEleme(ayrilmis):
    gecici = []
    urunMarkalari = ['COCA-COLA', 'PEPSI', 'FANTA', 'SPRITE', 'ULUDAĞ', 'TORKU', 'COCA', 'SCHWEPPES', 'FRUKO', 'RED', 'YEDIGÜN', 'ÇAMLICA', 'BURN', 'BEYOĞLU', 'MALTANA', 'BLACK', 'TURKA', 'COCACOLA']
    icecekAyrinti = ['ZERO', 'PORTAKAL', 'LIGHT', 'NO', 'ON', 'TONIK', 'TWIST', 'ŞEKERSIZ', 'MANDARIN', 'LIMON', 'MISKET', 'LIMONU', 'TONIC', 'MANDALINA', 'GOLD', 'LIMON-TA', 'ZENCEFILLI', 'BLUE', 'COSMOPOLITAN', 'YABAN', 'MERSINI', 'SIFIR', 'PINA', 'COLADA', 'AHUDUDU', 'TROPIKAL', 'MOJITO', 'ŞEFTALI', 'NAR', 'PORTAKAL', 'TURUNÇGILLER', 'BODRUM', 'ZENCEFIL', 'MOCKTAIL', 'MANGO', 'GINSENG', 'ANANAS', 'RUFFLES', 'NEXT', 'SIMPLY', 'VIVA', 'MATE', 'ENERGY', 'KAN', 'PORTAKALI', 'MADEN', 'SUYU', 'KARPUZ', 'REYHANLI', 'GINGER', 'ALE', 'ELMALI', 'ÇILEK']
    icecekAgirlik = ['4X1', '1,5', '2X1', '6X250', '2,5', '1', '250', '1.5', '2.5', '200', '4X250', '330', '6X200', '450', '1L', '500', '9X250', '250ML', '1.25', '6X450ML', '355', '473', '750', '2']
    marka=''
    ayrinti=''
    agirlik=''
    for kelime in ayrilmis:
        bulunan = arama(ayrilmis[0], urunMarkalari)
        if bulunan != '':
            bulunan = arama(kelime, urunMarkalari)
            if bulunan != '':
                marka = bulunan
                if marka=='COCA':
                    marka = 'COCA-COLA'
                elif marka == 'COCACOLA':
                    marka = 'COCA-COLA'
                elif marka == 'BLACK':
                    marka = 'BLACK BRUIN'
                elif marka == 'RED':
                    marka = 'RED BULL'
            else:
                bulunan = arama(kelime, icecekAyrinti)
                if bulunan!='':
                    ayrinti=ayrinti+' '+bulunan
                else:
                    bulunan= arama(kelime, icecekAgirlik)
                    if bulunan.strip()!='':
                        if agirlik== '1,5':
                            agirlik = '1.5' 
                            print(agirlik)
                        elif agirlik == '2,5':
                            agirlik = '2.5'
                        elif agirlik == '1L':
                            agirlik = '1'
                        elif agirlik == '250ML':
                            agirlik = '250' 
                        elif agirlik == '6X450ML':
                            agirlik = '6X450'
                            print(agirlik)
                        agirlik=bulunan
    ayrinti= ayrinti.strip()
    if ayrinti == 'GINGER ALE' or ayrinti == 'GINGER ALE ZENCEFIL':
        ayrinti = 'ZENCEFILLI'
    gecici.extend([marka,ayrinti,agirlik])
    #print(gecici)
    return gecici

def peynirIsimEleme(ayrilmis):
    gecici = []

    peynirMarkalari = ['BAHÇIVAN', 'TAHSILDAROĞLU', 'PINAR', 'İÇIM', 'ALTINKILIÇ', 'DOĞRULUK', 'EKICI', 'HASMANDIRA', 'KARPER', 'LAZ', 'MURATBEY', 'PRESIDENT', 'SÜTAŞ', 'TEKSÜT', 'TORKU']
    #peynirTuru = ['ÇEÇIL', 'DILIMLI', 'TOST', 'HELLIM', 'BEYAZ', 'ESKI', 'LIGHT', 'MOZZARELLA', 'RENDE', 'LABNE', 'TOPLARI', 'ÇEÇIL', 'GURME', 'BEYAZ', 'KREM', 'TAZE', 'PARMESAN', 'LAKTOZSUZ', ]
    peynirkAgirlik = ['225', '420', '350', '200', '125', 'KG',
                      '400', '450', '500', '500G', '600', '900', '250', '100', '300', '8X15', '8X20', '180', '3X180', '324', '750', '525', '700', '2X180', '160', '800', '80', '110', '60', '2X200', '220', '140', '1', '400GR', '375GR', '375', '250GR', '360', '270', '275', '300G', '1000', '108', '525G', '20', '1200']
    marka=''
    ayrinti=''
    agirlik=''
    for kelime in ayrilmis:
        bulunan = arama(ayrilmis[0], peynirMarkalari)
        if bulunan != '':
            bulunan = arama(kelime, peynirMarkalari)
            if bulunan != '':
                marka = bulunan
            else:
                bulunan = arama(kelime, peynirkAgirlik)
                if bulunan != '':
                    if bulunan == 'KG':
                        bulunan = '1'
                    elif bulunan == '500G':
                        bulunan = '500'
                    elif bulunan == '400GR':
                        bulunan = '400'
                    elif bulunan == '375GR':
                        bulunan = '375' 
                    elif bulunan == '250GR':
                        bulunan = '250' 
                    elif bulunan == '300G':
                        bulunan = '300' 
                    elif bulunan == '1000':
                        bulunan = '1' 
                    elif bulunan == '525G':
                        bulunan = '525' 
                    elif bulunan == '1200':
                        bulunan = '1.2'
                    agirlik = bulunan
                else:
                    if kelime != '':
                        if kelime != 'G' and kelime != 'GR' and kelime != 'PEYNIR' and kelime != 'PEYNIRI' and kelime != 'D-VITAMINLI':
                            if kelime == 'LEZZETLI':
                                kelime = 'LEZZET'
                            elif kelime == 'MIXLERI':
                                kelime = 'KARIŞIK'
                            ayrinti = ayrinti + ' ' + kelime
    ayrinti = ayrinti.strip()
    """ if ayrinti != '':
        ayrinti = ayrinti + ' ' + 'PEYNIRI' """
    #ayrinti = ayrinti.strip()
    gecici.extend([marka,ayrinti,agirlik])
    return gecici

def makarnaIsimEleme(ayrilmis):
    gecici = []
    makarnaMarkalari = ['PASTAVILLA', 'FILIZ', 'BARILLA', "NUH'UN", 'ARBELLA', 'INDOMIE', 'VERONELLI', 'NUHUN', 'KNORR', 'MUTLU', 'BANETTI', 'OBA' ]
    makarnaAgirlik = ['500', '350', '67', '400', '75', '400GR', '500GR', '66', '350GR', '70', '206', '120', '80', '65', '60G', '160', '250', '60', '210G']

    marka = ''
    ayrinti = ''
    agirlik = ''
    for kelime in ayrilmis:
        bulunan = arama(ayrilmis[0], makarnaMarkalari)
        if bulunan != '':
            bulunan = arama(kelime, makarnaMarkalari)
            if bulunan != '':
                if bulunan == "NUH'UN":
                    bulunan = 'NUHUN'
                marka = bulunan
                #print(ayrilmis)
                #return ayrilmis
            else:
                bulunan = arama(kelime, makarnaAgirlik)
                if bulunan != '':
                    if bulunan == '400GR':
                        bulunan = '400' 
                    elif bulunan == '500GR':
                        bulunan = '500'
                    elif bulunan == '350GR':
                        bulunan = '350'
                    elif bulunan == '60G':
                        bulunan = '60' 
                    elif bulunan == '210G':
                        bulunan = '210'
                    agirlik = bulunan
                else:
                    kelime = kelime.replace(')', '')
                    kelime = kelime.replace('(', '')
                    if kelime != 'GR' and kelime != 'MAKARNA' and kelime != 'ANKARA' and kelime != 'G' and kelime != 'ÇABUK' and kelime != 'NOODLE' and kelime != 'SEDANI' and kelime != 'RIGATI' and kelime != 'HAZIR' and kelime != 'POŞET' and kelime != 'BARDAK' and kelime != 'NO:5' and kelime != 'NO.13' and kelime != 'FARFALLE' and kelime != 'RISONI' and kelime != 'PIPE' and kelime != 'RIGATE' and kelime != 'GEMISI' and kelime != 'FETTUCCINE' and kelime != 'NODDLE' and kelime != 'MIE':
                        #and kelime != '(SPAGHETTI)' and kelime != '(KALEM)' and kelime != '(BARDAK)'
                        if kelime == '&':
                            kelime = 'AND'
                        elif kelime == 'KORILI':
                            kelime = 'KÖRILI'
                        elif kelime == 'KÖRI':
                            kelime = 'KÖRILI'
                        elif kelime == 'KORI':
                            kelime = 'KÖRILI'
                        ayrinti = ayrinti + ' ' + kelime
    ayrinti = ayrinti.strip()
    if 'SPAGHETTI' in ayrinti:
        if 'SPAGETTI' in ayrinti:
            ayrinti = ayrinti.replace('SPAGHETTI','')
        else:
            ayrinti = ayrinti.replace('SPAGHETTI', 'SPAGETTI')
    if ayrinti == 'LAZANYA LASAGNE':
        ayrinti = 'LAZANYA'
    elif ayrinti == 'LASAGNE':
        ayrinti = 'LAZANYA'
    gecici.extend([marka, ayrinti, agirlik])
    """ if gecici != ['','','']:
        print(gecici) """
    return gecici


def urunBilgi(isim, belirtec, aranan, agSayfasi, baglantiAdresi, urunIcerik, urunKodAd, urunKodFiyat, urunDizisi):
    #print(isim+' '+aranan+' '+agSayfasi+' '+baglantiAdresi)
    sayac = 1
    ilerlemePenceresi = wx.ProgressDialog('Ürün Bilgileri Alınıyor --- ('+isim+', '+aranan+')', str(sayac)+'. sayfa bilgileri alınıyor... ', -1, None, wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    ilerlemePenceresi.Pulse(str(sayac) + '. sayfa bilgileri alınıyor... ')
    wx.Yield()
    baglanti = baglantiAdresi+agSayfasi+str(sayac)
    oturum = HTMLSession()
    cevap = oturum.get(baglanti)
    cevap.html.render(timeout=60)
    corba = bs(cevap.html.html, 'html.parser')
    urunler = corba.find_all(urunIcerik[0], {urunIcerik[1]: urunIcerik[2]})
    while urunler != []:
        ilerlemePenceresi.Pulse(str(sayac) + '. sayfa bilgileri alınıyor... ')
        wx.Yield()
        print(str(sayac)+'. sayfa bilgileri alınıyor... ('+isim+', '+aranan+')')
        for urun in urunler:
            try:
                urunAd = urun.find(urunKodAd[0], {urunKodAd[1]: urunKodAd[2]}).string.upper().strip()
                urunFiyat = urun.find(urunKodFiyat[0], {urunKodFiyat[1], urunKodFiyat[2]}).text.strip()
            except AttributeError as hata:
                wx.MessageDialog(None, 'Ürünleri almada hata oluştu.\n('+isim+', '+aranan+')'+str(hata),'HATA', wx.OK | wx.ICON_ERROR).ShowModal()
                return 0
            else:
                urunFiyat = re.findall(r'(?<![a-zA-Z:])[-+]?\d*\.?\d+', urunFiyat)
                urunFiyat = str(urunFiyat[0])+','+str(urunFiyat[1])
                ayrilmis = urunAd.split()
                #print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
                #print(ayrilmis)
                if belirtec == 0 or belirtec == 4:
                    gecici = siviYagIsimEleme(ayrilmis)
                if belirtec == 1 or belirtec == 4:
                    gecici = icecekIsimEleme(ayrilmis)
                if belirtec==2 or belirtec == 4:
                    gecici = peynirIsimEleme(ayrilmis)
                if belirtec == 3 or belirtec == 4:
                    gecici = makarnaIsimEleme(ayrilmis)
                #print(gecici)
                #print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
                if belirtec == 0 or belirtec == 4:
                    if gecici != ['', '', '', ''] :
                        #print(gecici)
                        #print('-----------------------------------------------------------------------')
                        #print(len(gecici))
                        for sira, kelime in enumerate(gecici):
                            if sira != (len(gecici) - 1):
                                if kelime == '1' or kelime == '2' or kelime == '3' or kelime == '4' or kelime == '5':
                                    gecici.remove(kelime)
                        gecici.extend([urunFiyat])
                        urunDizisi.extend([gecici])
                elif belirtec == 1 or belirtec == 4:
                    if gecici != ['', '', '']:
                        gecici.extend([urunFiyat])
                        urunDizisi.extend([gecici])
                elif belirtec == 2 or belirtec == 4:
                    if gecici != ['', '', '']:
                        gecici.extend([urunFiyat])
                        urunDizisi.extend([gecici])
                elif belirtec == 3 or belirtec == 4:
                    if gecici != ['', '', '']:
                        gecici.extend([urunFiyat])
                        urunDizisi.extend([gecici])
        sayac = sayac + 1
        baglanti = baglantiAdresi+agSayfasi+str(sayac)
        oturum = HTMLSession()
        cevap = oturum.get(baglanti)
        cevap.html.render(timeout=60)
        corba = bs(cevap.html.html, 'html.parser')
        urunler = corba.find_all(urunIcerik[0], {urunIcerik[1]: urunIcerik[2]})
        cevap.close()
        oturum.close()
    """ for u in urunDizisi:
        print(u) """
    cevap.close()
    oturum.close()
    return 1

def secilenUrunMarketBilgisi(aranan, agSayfasi1, agSayfasi2, agSayfasi3, belirtec):
    global migrosUrunler
    global aUrunler
    global cagriUrunler
    migrosUrunler = []
    aUrunler = []
    cagriUrunler = []

    UrunIcerik = ['mat-card', 'class', 'mat-mdc-card mdc-card']
    UrunIcerikAd = ['a', 'class', 'mat-caption text-color-black product-name']
    UrunIcerikFiyat = ['span', 'class', 'amount']
    onay = urunBilgi('Migros', belirtec, aranan, cmSayfa, agSayfasi1, UrunIcerik, UrunIcerikAd, UrunIcerikFiyat, migrosUrunler)
    #print(migrosUrunler)
    if onay==0:
        return onay

    UrunIcerik = ['div', 'class', 'product-desc']
    UrunIcerikAd = ['h3', 'class', 'name']
    UrunIcerikFiyat = ['span', 'class', 'current']
    onay = urunBilgi('A101', belirtec, aranan, aSayfa, agSayfasi2, UrunIcerik, UrunIcerikAd, UrunIcerikFiyat, aUrunler)
    #print(aUrunler)
    if onay == 0:
        return onay

    UrunIcerik = ['div', 'class', 'productItem']
    UrunIcerikAd = ['div', 'class', 'productName detailUrl']
    UrunIcerikFiyat = ['div', 'class', 'discountPrice']
    onay = urunBilgi('Çağrı', belirtec, aranan, cmSayfa, agSayfasi3, UrunIcerik, UrunIcerikAd, UrunIcerikFiyat, cagriUrunler)
    if onay == 0:
        return onay
    #for x in cagriUrunler:
    #    print(x)
    """ print('ÇAĞRI---------------------------')
    for u in cagriUrunler:
        print(u)
    print('')
    print('A101---------------------------')
    for u in aUrunler:
        print(u)
    print('')
    print('MİGROS---------------------------')
    for u in migrosUrunler:
        print(u)
    print('------------------') """
    return onay

def urunlerinBilgileriniGetir(belirtec):
    if belirtec == 0 or belirtec == 4:
        onay = secilenUrunMarketBilgisi('Sıvı Yağ', migrosSiviYag, aSiviYag, cagriSiviYag, 0)
        if onay == 0:
            return onay
    if belirtec == 1 or belirtec == 4:
        onay = secilenUrunMarketBilgisi('İçecek', migrosGaz, aGaz, cagriGaz, 1)
        if onay == 0:
            return onay
    if belirtec==2 or belirtec == 4:
        onay = secilenUrunMarketBilgisi('Peynir', migrosPeynir, aPeynir, cagriPeynir, 2)
        if onay == 0:
            return onay
    if belirtec == 3 or belirtec == 4:
        onay = secilenUrunMarketBilgisi('Makarna', migrosMakarna, aMakarna, cagriMakarna, 3)
        if onay == 0:
            return onay
    return onay
############################################################################
########################---GRAFİK ÇİZDİRME---########################
def grafCiz(sayi, belirtec):
    if belirtec == 0:
        komut = '''select tarih,migFiyat,aFiyat,caFiyat from yagFiyatT where urunSira=?'''
    elif belirtec == 1:
        komut = '''select tarih,migFiyat,aFiyat,caFiyat from icecekFiyatT where urunSira=?'''
    elif belirtec == 2:
        komut = '''select tarih,migFiyat,aFiyat,caFiyat from peynirFiyatT where urunSira=?'''
    elif belirtec == 3:
        komut = '''select tarih,migFiyat,aFiyat,caFiyat from makarnaFiyatT where urunSira=?'''
    
    baglanti = veriTabaninaBaglan()
    if baglanti != None:
        try:
            imlec = baglanti.cursor()
        except Error as hata:
            wx.MessageDialog(None, 'İmleç oluşturmada hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
            return 0
        else:
            try:
                imlec.execute(komut,((sayi,)))
            except Error as hata:
                wx.MessageDialog(None, 'Ürün bilgisi çekilemedi.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                return 0
            else:
                urun = imlec.fetchall()
                print(urun)
                tarihDizi = []
                mFiyatlar = []
                aFiyatlar = []
                cFiyatlar = []
                for u in urun:
                    tarih = datetime.datetime.strptime(u[0], '%d-%m-%Y %H:%M:%S').date()
                    tarihDizi.extend([tarih])
                    if u[1]=='-':
                        mF = 0
                    else:
                        mF = float(u[1].replace(',','.'))
                    mFiyatlar.extend([mF])
                    
                    if u[2] == '-':
                        aF = 0
                    else:
                        aF = float(u[2].replace(',', '.'))
                    aFiyatlar.extend([aF])

                    if u[3] == '-':
                        cF = 0
                    else:
                        cF = float(u[3].replace(',', '.'))
                    cFiyatlar.extend([cF])
                print(tarihDizi)
                baglanti.close()

                tarihDizi = np.array(tarihDizi)
                mFiyatlar = np.array(mFiyatlar)
                aFiyatlar = np.array(aFiyatlar)
                cFiyatlar = np.array(cFiyatlar)
                ciz.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
                ciz.gca().xaxis.set_major_locator(mdates.DayLocator())
                ciz.plot(tarihDizi, mFiyatlar)
                ciz.plot(tarihDizi, aFiyatlar)
                ciz.plot(tarihDizi, cFiyatlar)
                ciz.legend(['Migros', 'A101', 'Çağrı'])
                ciz.gcf().autofmt_xdate()
                ciz.xlabel('Tarih')
                ciz.ylabel('Fiyat')
                ciz.show()
                return 1
#####################################################################
###################---KULLANICI ARAYÜZÜ---###################
def basariliMi():
    sayac = 0
    if migrosUrunler != []:
        sayac = sayac + 1
    if aUrunler != []:
        sayac = sayac + 1
    if cagriUrunler != []:
        sayac = sayac + 1
    
    if sayac > 0:
        wx.MessageDialog(None, 'Ürünler başarılı bir şekilde alındı.', 'OLDU!', wx.OK | wx.ICON_INFORMATION).ShowModal()
        print(sayac)
        print(str(len(migrosUrunler))+', '+str(len(aUrunler))+', '+str(len(cagriUrunler)))
        return 1
    else:
        wx.MessageDialog(None, 'Ürünler sayfalardan alınamadı.', 'OLMADI!', wx.OK | wx.ICON_ERROR).ShowModal()
        return 0

def karsilastir(ilk, ikinci):
    oran = fuzz.token_sort_ratio(ilk, ikinci)
    #print(ilk +', '+ikinci+', '+ str(oran))
    return oran


def yagUrunleriBirlestir():
    global cekilenOrtakUrunler
    global migrosUrunler
    global aUrunler
    global cagriUrunler
    cekilenOrtakUrunler=[]

    #print('Migros Önce: ' + str(len(migrosUrunler)))
    #print('A101 Önce: ' + str(len(aUrunler)))
    for ilk in migrosUrunler:
        for ikinci in aUrunler:
            if ilk[0] == ikinci[0] and ilk[1] == ikinci[1] and ilk[2] == ikinci[2] and ilk[3] == ikinci[3]:
                try:
                    ilk[5] = ikinci[-1]
                except IndexError:
                    ilk.extend([ikinci[-1], '-'])
                finally:
                    cekilenOrtakUrunler.extend([ilk])
                    migrosUrunler.remove(ilk)
                    aUrunler.remove(ikinci)
    #print('Migros Sonra: ' + str(len(migrosUrunler)))
    #print('A101 Sonra: ' + str(len(aUrunler)))

    #print('//////////////////////////////////////////////////////////')

    #print('Çağrı Önce: ' + str(len(cagriUrunler)))
    for ilk in cekilenOrtakUrunler:
        for ikinci in cagriUrunler:
            if ilk[0] == ikinci[0] and ilk[1] == ikinci[1] and ilk[2] == ikinci[2] and ilk[3] == ikinci[3]:
                try:
                    ilk[6] = ikinci[-1]
                except IndexError:
                    ilk.extend([ikinci[-1]])
                finally:
                    cagriUrunler.remove(ikinci)
    #print('Çağrı Sonra: ' + str(len(cagriUrunler)))

    #print('//////////////////////////////////////////////////////////')

    #print('Çekilen Önce: ' + str(len(cekilenOrtakUrunler)))
    #print('Migros Önce: ' + str(len(migrosUrunler)))
    #print('Çağrı Önce: ' + str(len(cagriUrunler)))
    for ilk in migrosUrunler:
        for ikinci in cagriUrunler:
            if ilk[0] == ikinci[0] and ilk[1] == ikinci[1] and ilk[2] == ikinci[2] and ilk[3] == ikinci[3]:
                try:
                    ilk[6] = ikinci[-1]
                except IndexError:
                    ilk.extend(['-', ikinci[-1]])
                finally:
                    cekilenOrtakUrunler.extend([ilk])
    #print('Migros Sonra: ' + str(len(migrosUrunler)))
    #print('Çağrı Sonra: ' + str(len(cagriUrunler)))
    #print('Çekilen Sonra: ' + str(len(cekilenOrtakUrunler)))

    #print('//////////////////////////////////////////////////////////')

    #print('Çekilen Önce: ' + str(len(cekilenOrtakUrunler)))
    #print('A101 Önce: ' + str(len(aUrunler)))
    #print('Çağrı Önce: ' + str(len(cagriUrunler)))
    for ilk in aUrunler:
        for ikinci in cagriUrunler:
            if ilk[0] == ikinci[0] and ilk[1] == ikinci[1] and ilk[2] == ikinci[2] and ilk[3] == ikinci[3]:
                try:
                    ilk[6] = ikinci[-1]
                except IndexError:
                    ilk.insert(4, '-')
                    ilk.extend([ikinci[-1]])
                finally:
                    cekilenOrtakUrunler.extend([ilk])
    #print('A101 Sonra: ' + str(len(aUrunler)))
    #print('Çağrı Sonra: ' + str(len(cagriUrunler)))
    #print('Çekilen Sonra: ' + str(len(cekilenOrtakUrunler)))

    """ print('-----------------------------------------------------')
    for a in cekilenOrtakUrunler:
        print(a)
    print('-----------------------------------------------------') """

def icecekUrunleriBirlestir():
    global cekilenOrtakUrunler
    global migrosUrunler
    global aUrunler
    global cagriUrunler
    cekilenOrtakUrunler = []
    birlesim = []

    for sayac1, ilk in enumerate(migrosUrunler):
        for sayac2,ikinci in enumerate(aUrunler):
            if ilk[0] == ikinci[0] and ilk[2] == ikinci[2]:
                oran = karsilastir(ilk[1], ikinci[1])
                if oran > 89:
                    gecici = [ilk, ikinci]
                    birlesim.extend([ilk])
                    del migrosUrunler[sayac1]
                    del aUrunler[sayac2]
                    cekilenOrtakUrunler.extend([gecici])

    if birlesim != []:
        for ilk in birlesim:
            for sayac2, ikinci in enumerate(cagriUrunler):
                if ilk[0] == ikinci[0] and ilk[2] == ikinci[2]:
                    oran = karsilastir(ilk[1], ikinci[1])
                    if oran > 89:
                        for a in cekilenOrtakUrunler:
                            if a[0][0] == ikinci[0] and a[0][1] == ikinci[1] and a[0][2] == ikinci[2]:
                                a.extend([ikinci])
                        cagriUrunler.remove(cagriUrunler[sayac2])

    for ilk in migrosUrunler:
        for ikinci in cagriUrunler:
            if ilk[0] == ikinci[0] and ilk[2] == ikinci[2]:
                oran = karsilastir(ilk[1], ikinci[1])
                if oran > 89:
                    gecici = [ilk, ['-', '-', '-', '-'], ikinci]
                    cekilenOrtakUrunler.extend([gecici])

    for ilk in cagriUrunler:
        for ikinci in aUrunler:
            if ilk[0] == ikinci[0] and ilk[2] == ikinci[2]:
                oran = karsilastir(ilk[1], ikinci[1])
                if oran > 89:
                    gecici = [['-', '-', '-', '-'], ilk, ikinci]
                    cekilenOrtakUrunler.extend([gecici])

    for eklenecek in cekilenOrtakUrunler:
        if len(eklenecek) == 2:
            eklenecek.extend([['-', '-', '-', '-']])

    ckGecici = cekilenOrtakUrunler
    for bak in ckGecici:
        sayac = 0
        for s1, silinecek in enumerate(cekilenOrtakUrunler):
            if bak == silinecek:
                sayac = sayac + 1
                if sayac > 1:
                    del cekilenOrtakUrunler[s1]

    print(str(len(cekilenOrtakUrunler)))
    print('-----------------------------------------------------')
    #asd = cekilenOrtakUrunler
    #for a in asd:
    #    sayac = 0
    #    for b in cekilenOrtakUrunler:
    #        if a==b:
    #            sayac = sayac + 1
    #        if sayac > 1:
    #            print(b)
            

    for a in cekilenOrtakUrunler:
        print(a)
    print('-----------------------------------------------------')
    print('asd')

def peynirUrunleriBirlestir():
    global cekilenOrtakUrunler
    global migrosUrunler
    global aUrunler
    global cagriUrunler
    cekilenOrtakUrunler = []
    birlesim =[]

    for ilk in migrosUrunler:
        for ikinci in aUrunler:
            if ilk[0] == ikinci[0] and ilk[2] == ikinci[2]:
                oran = karsilastir(ilk[1], ikinci[1])
                if oran > 89:
                    gecici = [ilk, ikinci]
                    birlesim.extend([ilk])
                    migrosUrunler.remove(ilk)
                    aUrunler.remove(ikinci)
                    cekilenOrtakUrunler.extend([gecici])
    
    for ilk in birlesim:
        for ikinci in cagriUrunler:
            if ilk[0] == ikinci[0] and ilk[2] == ikinci[2]:
                oran = karsilastir(ilk[1], ikinci[1])
                if oran > 89:
                    for a in cekilenOrtakUrunler:
                        if a[0][0] == ikinci[0] and a[0][1] == ikinci[1] and a[0][2] == ikinci[2]:
                            a.extend([ikinci])
                    cagriUrunler.remove(ikinci)

    for ilk in migrosUrunler:
        for ikinci in cagriUrunler:
            if ilk[0] == ikinci[0] and ilk[2] == ikinci[2]:
                oran = karsilastir(ilk[1], ikinci[1])
                if oran > 89:
                    gecici = [ilk, ['-', '-', '-', '-'], ikinci]
                    cekilenOrtakUrunler.extend([gecici])
    
    for ilk in cagriUrunler:
        for ikinci in aUrunler:
            if ilk[0] == ikinci[0] and ilk[2] == ikinci[2]:
                oran = karsilastir(ilk[1], ikinci[1])
                if oran > 89:
                    gecici = [['-', '-', '-', '-'], ilk, ikinci]
                    cekilenOrtakUrunler.extend([gecici])

    for eklenecek in cekilenOrtakUrunler:
        if len(eklenecek) == 2:
            eklenecek.extend([['-', '-', '-', '-']])
    
    ckGecici = cekilenOrtakUrunler
    for bak in ckGecici:
        sayac = 0
        for silinecek in cekilenOrtakUrunler:
            if bak == silinecek:
                sayac = sayac + 1
                if sayac > 1:
                    cekilenOrtakUrunler.remove(silinecek)
    

    """ print(str(len(cekilenOrtakUrunler)))
    print('-----------------------------------------------------')
    for a in cekilenOrtakUrunler:
        print(a)
    print('-----------------------------------------------------')
    print('asd') """

def makarnaUrunleriBirlestir():
    global cekilenOrtakUrunler
    global migrosUrunler
    global aUrunler
    global cagriUrunler
    cekilenOrtakUrunler = []
    birlesim = []
    for ilk in migrosUrunler:
        for ikinci in aUrunler:
            if ilk[0] == ikinci[0] and ilk[2] == ikinci[2]:
                oran = karsilastir(ilk[1], ikinci[1])
                if oran > 89:
                    gecici = [ilk, ikinci]
                    birlesim.extend([ilk])
                    migrosUrunler.remove(ilk)
                    aUrunler.remove(ikinci)
                    cekilenOrtakUrunler.extend([gecici])

    for ilk in birlesim:
        for ikinci in cagriUrunler:
            if ilk[0] == ikinci[0] and ilk[2] == ikinci[2]:
                oran = karsilastir(ilk[1], ikinci[1])
                if oran > 89:
                    for a in cekilenOrtakUrunler:
                        if a[0][0] == ikinci[0] and a[0][1] == ikinci[1] and a[0][2] == ikinci[2]:
                            a.extend([ikinci])
                    cagriUrunler.remove(ikinci)

    for ilk in migrosUrunler:
        for ikinci in cagriUrunler:
            if ilk[0] == ikinci[0] and ilk[2] == ikinci[2]:
                oran = karsilastir(ilk[1], ikinci[1])
                if oran > 89:
                    gecici = [ilk, ['-', '-', '-', '-'], ikinci]
                    cekilenOrtakUrunler.extend([gecici])

    for ilk in cagriUrunler:
        for ikinci in aUrunler:
            if ilk[0] == ikinci[0] and ilk[2] == ikinci[2]:
                oran = karsilastir(ilk[1], ikinci[1])
                if oran > 89:
                    gecici = [['-', '-', '-', '-'], ilk, ikinci]
                    cekilenOrtakUrunler.extend([gecici])

    for eklenecek in cekilenOrtakUrunler:
        if len(eklenecek) == 2:
            eklenecek.extend([['-', '-', '-', '-']])

    ckGecici = cekilenOrtakUrunler
    for bak in ckGecici:
        sayac = 0
        for silinecek in cekilenOrtakUrunler:
            if bak == silinecek:
                sayac = sayac + 1
                if sayac > 1:
                    cekilenOrtakUrunler.remove(silinecek)

    """ print(str(len(cekilenOrtakUrunler)))
    print('-----------------------------------------------------')
    #asd = cekilenOrtakUrunler
    #for a in asd:
    #    sayac = 0
    #    for b in cekilenOrtakUrunler:
    #        if a==b:
    #            sayac = sayac + 1
    #        if sayac > 1:
    #            print(b)
            

    for a in cekilenOrtakUrunler:
        print(a)
    print('-----------------------------------------------------')
    print('asd') """


def urunleriVtEkle(secilen):
    baglanti = veriTabaninaBaglan()
    if baglanti != None:
        if veriTabaniTablo(baglanti):
            if secilen == 0 or secilen == 4:
                yagUrunleriBirlestir()
                if verileriTabloyaEkle(baglanti, 0):
                    #print('sayi : '+str(len(cekilenOrtakUrunler)))
                    wx.MessageDialog(None, str(len(cekilenOrtakUrunler)) + ' tane yağ verisi eklendi.','BAŞARILI', wx.OK|wx.ICON_INFORMATION).ShowModal()
            if secilen == 1 or secilen == 4:
                icecekUrunleriBirlestir()
                if verileriTabloyaEkle(baglanti, 1):
                    #print('sayi : '+str(len(cekilenOrtakUrunler)))
                    wx.MessageDialog(None, str(len(cekilenOrtakUrunler)) + ' tane içecek veri eklendi.','BAŞARILI', wx.OK|wx.ICON_INFORMATION).ShowModal()
            if secilen == 2 or secilen == 4:
                peynirUrunleriBirlestir()
                if verileriTabloyaEkle(baglanti, 2):
                    #print('sayi : '+str(len(cekilenOrtakUrunler)))
                    wx.MessageDialog(None, str(len(cekilenOrtakUrunler)) + ' tane içecek veri eklendi.','BAŞARILI', wx.OK|wx.ICON_INFORMATION).ShowModal()
            if secilen == 3 or secilen == 4:
                makarnaUrunleriBirlestir()
                if verileriTabloyaEkle(baglanti, 3):
                    #print('sayi : '+str(len(cekilenOrtakUrunler)))
                    wx.MessageDialog(None, str(len(cekilenOrtakUrunler)) + ' tane içecek veri eklendi.','BAŞARILI', wx.OK|wx.ICON_INFORMATION).ShowModal()

def sorguIcinUrunBilgi(secim):
    ad=[]
    ayrinti=[]
    tur=[]
    agirlik=[]
    urunSiralari = []
    if secim == 1:
        sorgu = '''select * from yagUrunleriT'''
        baglanti = veriTabaninaBaglan()
        if baglanti != None:
            try:
                imlec = baglanti.cursor()
            except Error as hata:
                wx.MessageDialog(None, 'İmleç oluşturmada hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
            else:
                try:
                    imlec.execute(sorgu)
                except Error as hata:
                    wx.MessageDialog(None, 'İsme göre ürün sırası arama hatası(Bilgi için).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                else:
                    urunler = imlec.fetchall()
                    for urun in urunler:
                        urunSiralari.extend([urun[0]])
                        ad.extend([urun[1]])
                        if urun[2]!='':
                            ayrinti.extend([urun[2]])
                        tur.extend([urun[3]])
                        agirlik.extend([urun[4]])
            ad = list(set(ad))
            ayrinti = list(set(ayrinti))
            tur = list(set(tur))
            agirlik = list(set(agirlik))
            ad.insert(0,'Farketmez')
            ayrinti.insert(0, 'Farketmez')
            tur.insert(0,'Farketmez')
            agirlik.insert(0, 'Farketmez')
        return ad, ayrinti, tur, agirlik
    elif secim == 2:
        sorgu = '''select * from icecekUrunleriT'''
        baglanti = veriTabaninaBaglan()
        if baglanti != None:
            try:
                imlec = baglanti.cursor()
            except Error as hata:
                wx.MessageDialog(None, 'İmleç oluşturmada hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
            else:
                try:
                    imlec.execute(sorgu)
                except Error as hata:
                    wx.MessageDialog(None, 'İsme göre ürün sırası arama hatası(Bilgi için).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                else:
                    urunler = imlec.fetchall()
                    for urun in urunler:
                        urunSiralari.extend([urun[0]])
                        ad.extend([urun[1]])
                        if urun[2]!='':
                            ayrinti.extend([urun[2]])
                        agirlik.extend([urun[3]])
            ad = list(set(ad))
            ayrinti = list(set(ayrinti))
            agirlik = list(set(agirlik))
            ad.insert(0,'Farketmez')
            ayrinti.insert(0, 'Farketmez')
            agirlik.insert(0, 'Farketmez')
        return ad, ayrinti, agirlik
    elif secim == 3:
        sorgu = '''select * from peynirUrunleriT'''
        baglanti = veriTabaninaBaglan()
        if baglanti != None:
            try:
                imlec = baglanti.cursor()
            except Error as hata:
                wx.MessageDialog(None, 'İmleç oluşturmada hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
            else:
                try:
                    imlec.execute(sorgu)
                except Error as hata:
                    wx.MessageDialog(None, 'İsme göre ürün sırası arama hatası(Bilgi için).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                else:
                    urunler = imlec.fetchall()
                    for urun in urunler:
                        urunSiralari.extend([urun[0]])
                        ad.extend([urun[1]])
                        if urun[2]!='':
                            ayrinti.extend([urun[2]])
                        agirlik.extend([urun[3]])
            ad = list(set(ad))
            ayrinti = list(set(ayrinti))
            agirlik = list(set(agirlik))
            ad.insert(0,'Farketmez')
            ayrinti.insert(0, 'Farketmez')
            agirlik.insert(0, 'Farketmez')
        return ad, ayrinti, agirlik
    elif secim == 4:
        sorgu = '''select * from makarnaUrunleriT'''
        baglanti = veriTabaninaBaglan()
        if baglanti != None:
            try:
                imlec = baglanti.cursor()
            except Error as hata:
                wx.MessageDialog(None, 'İmleç oluşturmada hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
            else:
                try:
                    imlec.execute(sorgu)
                except Error as hata:
                    wx.MessageDialog(None, 'İsme göre ürün sırası arama hatası(Bilgi için).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                else:
                    urunler = imlec.fetchall()
                    for urun in urunler:
                        urunSiralari.extend([urun[0]])
                        ad.extend([urun[1]])
                        if urun[2]!='':
                            ayrinti.extend([urun[2]])
                        agirlik.extend([urun[3]])
            ad = list(set(ad))
            ayrinti = list(set(ayrinti))
            agirlik = list(set(agirlik))
            ad.insert(0,'Farketmez')
            ayrinti.insert(0, 'Farketmez')
            agirlik.insert(0, 'Farketmez')
        return ad, ayrinti, agirlik

class urunGoster(wx.Frame):
    def __init__(self, sahip, baslik, enlik, yukseklik, urunler, fiyatlar, belirtec):
        super(urunGoster, self).__init__(parent=sahip, title=baslik, size=(enlik, yukseklik))
        
        self.KA(urunler, fiyatlar, belirtec)

    def KA(self, urunler, fiyatlar, belirtec):
        self.Centre()
        kutu = wx.Panel(self)
        self.SetBackgroundColour(wx.Colour(7, 54, 66))

        self.verilerinListesi = wx.ListCtrl(kutu, style=wx.LC_REPORT, pos=(100, 100), size=(800, 500))
        self.verilerinListesi.SetBackgroundColour((238, 232, 213))
        
        if belirtec == 0:
            self.verilerinListesi.SetTextColour((101, 123, 131))
            self.verilerinListesi.InsertColumn(0, 'Sıra', width=50)
            self.verilerinListesi.InsertColumn(1, 'Marka Adı', width=100)
            self.verilerinListesi.InsertColumn(2, 'Ürün Ayrıntı', width=200)
            self.verilerinListesi.InsertColumn(3, 'Yağ Tipi', width=100)
            self.verilerinListesi.InsertColumn(4, 'Ağırlık(L/ML)', width=100)
            self.verilerinListesi.InsertColumn(5, 'Migros', width=75)
            self.verilerinListesi.InsertColumn(6, 'A101', width=75)
            self.verilerinListesi.InsertColumn(7, 'Çağrı', width=75)
            for urun in urunler:
                for fiyat in fiyatlar:
                    if fiyat[5] == urun[0]:
                        m = fiyat[2]
                        a = fiyat[3]
                        c = fiyat[4]
                self.verilerinListesi.InsertItem(0, str(urun[0]))
                self.verilerinListesi.SetItem(0, 1, urun[1])
                self.verilerinListesi.SetItem(0, 2, urun[2])
                self.verilerinListesi.SetItem(0, 3, urun[3])
                self.verilerinListesi.SetItem(0, 4,  urun[4]+' ML' if int(urun[4]) > 6 else urun[4]+' L')
                self.verilerinListesi.SetItem(0, 5, m)
                self.verilerinListesi.SetItem(0, 6, a)
                self.verilerinListesi.SetItem(0, 7, c)
                self.verilerinListesi.Bind(wx.EVT_LIST_ITEM_SELECTED, lambda olay: self.cizdir(olay, belirtec))
        elif belirtec == 1:
            self.verilerinListesi.SetTextColour((101, 123, 131))
            self.verilerinListesi.InsertColumn(0, 'Sıra', width=50)
            self.verilerinListesi.InsertColumn(1, 'Marka Adı', width=100)
            self.verilerinListesi.InsertColumn(2, 'Ürün Ayrıntı', width=300)
            self.verilerinListesi.InsertColumn(3, 'Ağırlık(L/ML)', width=100)
            self.verilerinListesi.InsertColumn(4, 'Migros', width=75)
            self.verilerinListesi.InsertColumn(5, 'A101', width=75)
            self.verilerinListesi.InsertColumn(6, 'Çağrı', width=75)
            for urun in urunler:
                for fiyat in fiyatlar:
                    if fiyat[5] == urun[0]:
                        m = fiyat[2]
                        a = fiyat[3]
                        c = fiyat[4]
                self.verilerinListesi.InsertItem(0, str(urun[0]))
                self.verilerinListesi.SetItem(0, 1, urun[1])
                self.verilerinListesi.SetItem(0, 2, urun[2])
                self.verilerinListesi.SetItem(0, 3,  urun[3])
                self.verilerinListesi.SetItem(0, 4, m)
                self.verilerinListesi.SetItem(0, 5, a)
                self.verilerinListesi.SetItem(0, 6, c)
                self.verilerinListesi.Bind(wx.EVT_LIST_ITEM_SELECTED, lambda olay: self.cizdir(olay, belirtec))
        elif belirtec == 2:
            self.verilerinListesi.SetTextColour((101, 123, 131))
            self.verilerinListesi.InsertColumn(0, 'Sıra', width=50)
            self.verilerinListesi.InsertColumn(1, 'Marka Adı', width=100)
            self.verilerinListesi.InsertColumn(2, 'Ürün Ayrıntı', width=300)
            self.verilerinListesi.InsertColumn(3, 'Ağırlık(Kg/Gr)', width=100)
            self.verilerinListesi.InsertColumn(4, 'Migros', width=75)
            self.verilerinListesi.InsertColumn(5, 'A101', width=75)
            self.verilerinListesi.InsertColumn(6, 'Çağrı', width=75)
            for urun in urunler:
                for fiyat in fiyatlar:
                    if fiyat[5] == urun[0]:
                        m = fiyat[2]
                        a = fiyat[3]
                        c = fiyat[4]
                self.verilerinListesi.InsertItem(0, str(urun[0]))
                self.verilerinListesi.SetItem(0, 1, urun[1])
                self.verilerinListesi.SetItem(0, 2, urun[2])
                self.verilerinListesi.SetItem(0, 3,  urun[3])
                self.verilerinListesi.SetItem(0, 4, m)
                self.verilerinListesi.SetItem(0, 5, a)
                self.verilerinListesi.SetItem(0, 6, c)
                self.verilerinListesi.Bind(wx.EVT_LIST_ITEM_SELECTED, lambda olay: self.cizdir(olay, belirtec))
        elif belirtec == 3:
            self.verilerinListesi.SetTextColour((101, 123, 131))
            self.verilerinListesi.InsertColumn(0, 'Sıra', width=50)
            self.verilerinListesi.InsertColumn(1, 'Marka Adı', width=100)
            self.verilerinListesi.InsertColumn(2, 'Ürün Ayrıntı', width=300)
            self.verilerinListesi.InsertColumn(3, 'Ağırlık(Kg/Gr)', width=100)
            self.verilerinListesi.InsertColumn(4, 'Migros', width=75)
            self.verilerinListesi.InsertColumn(5, 'A101', width=75)
            self.verilerinListesi.InsertColumn(6, 'Çağrı', width=75)
            for urun in urunler:
                for fiyat in fiyatlar:
                    if fiyat[5] == urun[0]:
                        m = fiyat[2]
                        a = fiyat[3]
                        c = fiyat[4]
                self.verilerinListesi.InsertItem(0, str(urun[0]))
                self.verilerinListesi.SetItem(0, 1, urun[1])
                self.verilerinListesi.SetItem(0, 2, urun[2])
                self.verilerinListesi.SetItem(0, 3,  urun[3]+' Gr' if int(urun[3]) > 6 else urun[3]+' Kg')
                self.verilerinListesi.SetItem(0, 4, m)
                self.verilerinListesi.SetItem(0, 5, a)
                self.verilerinListesi.SetItem(0, 6, c)
                self.verilerinListesi.Bind(wx.EVT_LIST_ITEM_SELECTED, lambda olay: self.cizdir(olay, belirtec))
        
        self.kapat = wx.Button(kutu, label='Kapat', pos=(890, 10), size=(100, 50), style=wx.BORDER_NONE)
        self.kapat.SetBackgroundColour((203, 75, 22))
        self.kapat.Bind(wx.EVT_BUTTON, self.cikis)

    def cikis(self, olay):
        self.Destroy()

    def cizdir(self, olay, belirtec):
        listeSayisi = self.verilerinListesi.GetFirstSelected()
        secilen = self.verilerinListesi.GetItem(itemIdx=listeSayisi, col=0)
        urunSira = secilen.GetText()
        print(urunSira)
        if not(grafCiz(urunSira, belirtec)):
            wx.MessageDialog(None, 'Ürünün grafiği çizilemedi.','HATA', wx.OK|wx.ICON_ERROR).ShowModal()
            


class anaPencere(wx.Frame):
    def __init__(self, sahip, baslik, enlik, yukseklik):
        super(anaPencere, self).__init__(parent=sahip, title=baslik, size=(enlik, yukseklik))
        self.KA()

    def KA(self):
        self.Centre()
        kutu = wx.Panel(self)
        self.SetBackgroundColour(wx.Colour(7, 54, 66))

        self.kapat = wx.Button(kutu, label='Kapat', pos=(890, 10), size=(100, 50), style=wx.BORDER_NONE)
        self.kapat.SetBackgroundColour((203, 75, 22))
        self.kapat.Bind(wx.EVT_BUTTON, self.cikis)

        self.urunBilgi=wx.Button(kutu,label='Ürün Bilgilerini Al',pos=(10,10),size=(150,50),style=wx.BORDER_NONE)
        self.urunBilgi.SetBackgroundColour((238, 232, 213))
        self.urunBilgi.Bind(wx.EVT_BUTTON, lambda olay: self.getirilecekBilgi(olay, kutu))
        ################-----------------ÜRÜN BİLGİ GETİR BUTONLARI (AŞAĞISI)-----------------################
        self.siviYagBilgi=wx.Button(kutu,label='Sıvı Yağ',pos=(10,65),size=(70,30),style=wx.BORDER_NONE)
        self.siviYagBilgi.Hide()
        self.siviYagBilgi.SetBackgroundColour((133,153,0))
        self.siviYagBilgi.SetOwnForegroundColour((7, 54, 66))
        self.siviYagBilgi.Bind(wx.EVT_BUTTON, self.yagBilgiGetir)

        self.icecekgBilgi=wx.Button(kutu,label='İçecek',pos=(90,65),size=(70,30),style=wx.BORDER_NONE)
        self.icecekgBilgi.Hide()
        self.icecekgBilgi.SetBackgroundColour((220,50,47))
        self.icecekgBilgi.SetOwnForegroundColour((7, 54, 66))
        self.icecekgBilgi.Bind(wx.EVT_BUTTON, self.icecekBilgiGetir)

        self.peynirBilgi=wx.Button(kutu,label='Peynir',pos=(170,65),size=(70,30),style=wx.BORDER_NONE)
        self.peynirBilgi.Hide()
        self.peynirBilgi.SetBackgroundColour((253, 246, 227))
        self.peynirBilgi.SetOwnForegroundColour((7, 54, 66))
        self.peynirBilgi.Bind(wx.EVT_BUTTON, self.peynirBilgiGetir)

        self.makarnaBilgi=wx.Button(kutu,label='Makarna',pos=(250,65),size=(70,30),style=wx.BORDER_NONE)
        self.makarnaBilgi.Hide()
        self.makarnaBilgi.SetBackgroundColour((238, 232, 213))
        self.makarnaBilgi.SetOwnForegroundColour((7, 54, 66))
        self.makarnaBilgi.Bind(wx.EVT_BUTTON, self.makarnaBilgiGetir)

        """ self.toptanBilgi=wx.Button(kutu,label='Hepsi',pos=(330,65) pos=(410,65),size=(70,30),style=wx.BORDER_NONE)
        self.toptanBilgi.Hide()
        self.toptanBilgi.SetBackgroundColour((181, 137, 0))
        self.toptanBilgi.SetOwnForegroundColour((7, 54, 66))
        self.toptanBilgi.Bind(wx.EVT_BUTTON, self.toptanBilgiGetir) """

        self.gizleBilgi=wx.Button(kutu,label='Gizle',pos=(330,65),size=(70,30),style=wx.BORDER_NONE)
        self.gizleBilgi.Hide()
        self.gizleBilgi.SetBackgroundColour((88, 110, 117))
        self.gizleBilgi.SetOwnForegroundColour((7, 54, 66))
        self.gizleBilgi.Bind(wx.EVT_BUTTON, self.gizleBilgiGetir)
        ################-----------------ÜRÜN BİLGİ GETİR BUTONLARI (YUKARISI)-----------------################
        ################-----------------SORGU ALANI (AŞAĞISI)-----------------################
        wx.StaticText(kutu, label = 'Ürün Türü', pos = (197, 15)).SetOwnForegroundColour((238, 232, 213))
        self.urunlerinTuru = wx.ComboBox(kutu, choices = ['Seçiniz','Yağ','İçecek','Peynir','Makarna'], size = (100, 30), pos = (190, 30))
        self.urunlerinTuru.Bind(wx.EVT_COMBOBOX, lambda olay: self.secimYapildi(olay, kutu))

        self.markaYazi = wx.StaticText(kutu, label = 'Marka', pos = (307, 15))
        self.markaYazi.SetOwnForegroundColour((238, 232, 213))
        self.markaYazi.Hide()
        self.urunMarka = wx.ComboBox(kutu, choices = [''], size = (100, 30), pos = (300, 30))
        self.urunMarka.Hide()

        self.ayrintiYazi = wx.StaticText(kutu, label = 'Ayrıntı', pos = (417, 15))
        self.ayrintiYazi.SetOwnForegroundColour((238, 232, 213))
        self.ayrintiYazi.Hide()
        self.urunAyrinti = wx.ComboBox(kutu, choices = [''], size = (100, 30), pos = (410, 30))
        self.urunAyrinti.Hide()

        self.turYazi = wx.StaticText(kutu, label = 'Türü', pos = (527, 15))
        self.turYazi.SetOwnForegroundColour((238, 232, 213))
        self.turYazi.Hide()
        self.urunTur = wx.ComboBox(kutu, choices = [''], size = (100, 30), pos = (520, 30))
        self.urunTur.Hide()

        self.agirlikYazi = wx.StaticText(kutu, label = 'Ağırlığı', pos = (637, 15))
        self.agirlikYazi.SetOwnForegroundColour((238, 232, 213))
        self.agirlikYazi.Hide()
        self.urunAgirlik = wx.ComboBox(kutu, choices = [''], size = (100, 30), pos = (630, 30))
        self.urunAgirlik.Hide()

        self.sorgula=wx.Button(kutu, label='Sorgula', pos=(740, 26), size=(70, 30),style=wx.BORDER_NONE)
        self.sorgula.SetBackgroundColour((88, 110, 117))
        self.sorgula.SetOwnForegroundColour((7, 54, 66))
        self.sorgula.Hide()
        self.sorgula.Bind(wx.EVT_BUTTON, self.urunBilgiGetir)

        ################-----------------SORGU ALANI (YUKARISI)-----------------################
        ################-----------------RESİM BUTONLARI (AŞAĞISI)-----------------################
        self.resim = wx.Bitmap("yag.png", wx.BITMAP_TYPE_ANY)
        self.resim = self.resim.ConvertToImage()
        self.resim = self.resim.Scale(140, 300, wx.IMAGE_QUALITY_HIGH)
        self.resim = wx.Bitmap(self.resim)
        self.yagResmi = wx.StaticBitmap(kutu,-1, self.resim, pos=(850, 160))
        self.yagResmi.Bind(wx.EVT_LEFT_DOWN, lambda olay: self.yagGetir(olay, kutu))

        self.resim = wx.Bitmap("icecek.png", wx.BITMAP_TYPE_ANY)
        self.resim = self.resim.ConvertToImage()
        self.resim = self.resim.Scale(210, 300, wx.IMAGE_QUALITY_HIGH)
        self.resim = wx.Bitmap(self.resim)
        self.icecekResmi = wx.StaticBitmap(kutu,-1, self.resim, pos=(580, 150))
        self.icecekResmi.Bind(wx.EVT_LEFT_DOWN, lambda olay: self.icecekGetir(olay, kutu))

        self.resim = wx.Bitmap("peynir.png", wx.BITMAP_TYPE_ANY)
        self.resim = self.resim.ConvertToImage()
        self.resim = self.resim.Scale(210, 300, wx.IMAGE_QUALITY_HIGH)
        self.resim = wx.Bitmap(self.resim)
        self.peynirResmi = wx.StaticBitmap(kutu,-1, self.resim, pos=(300, 150))
        self.peynirResmi.Bind(wx.EVT_LEFT_DOWN, lambda olay: self.peynirGetir(olay, kutu))

        self.resim = wx.Bitmap("makarna.png", wx.BITMAP_TYPE_ANY)
        self.resim = self.resim.ConvertToImage()
        self.resim = self.resim.Scale(300, 230, wx.IMAGE_QUALITY_HIGH)
        self.resim = wx.Bitmap(self.resim)
        self.makarnaResmi = wx.StaticBitmap(kutu,-1, self.resim, pos=(0, 200))
        self.makarnaResmi.Bind(wx.EVT_LEFT_DOWN, lambda olay: self.makarnaGetir(olay, kutu))
        ################-----------------RESİM BUTONLARI (YUKARISI)-----------------################

    def cikis(self, olay,):
        self.Destroy()

    def secimYapildi(self, olay, kutu):
        secim = self.urunlerinTuru.GetCurrentSelection()
        if secim==0:
            self.markaYazi.Hide()
            self.urunMarka.Hide()
            self.ayrintiYazi.Hide()
            self.urunAyrinti.Hide()
            self.turYazi.Hide()
            self.urunTur.Hide()
            self.agirlikYazi.Hide()
            self.urunAgirlik.Hide()
            self.sorgula.Hide()
        elif secim==1:
            self.urunMarka.Clear()
            self.urunAyrinti.Clear()
            self.urunTur.Clear()
            self.urunAgirlik.Clear()

            markalar, digerAdlar, yagTipleri, agirliklar = sorguIcinUrunBilgi(secim)

            self.urunMarka.Append(markalar)
            self.urunAyrinti.Append(digerAdlar)
            self.urunTur.Append(yagTipleri)
            self.urunAgirlik.Append(agirliklar)

            self.urunMarka.SetSelection(0)
            self.urunTur.SetSelection(0)
            self.urunAyrinti.SetSelection(0)
            self.urunAgirlik.SetSelection(0)

            self.markaYazi.Show()
            self.urunMarka.Show()
            self.ayrintiYazi.Show()
            self.urunAyrinti.Show()
            self.turYazi.Show()
            self.urunTur.Show()
            self.agirlikYazi.Show()
            self.urunAgirlik.Show()
            self.sorgula.Show()
        elif secim == 2:
            self.urunMarka.Clear()
            self.urunAyrinti.Clear()
            self.urunTur.Clear()
            self.urunAgirlik.Clear()

            markalar, digerAdlar, agirliklar = sorguIcinUrunBilgi(secim)

            self.urunMarka.Append(markalar)
            self.urunAyrinti.Append(digerAdlar)
            self.urunAgirlik.Append(agirliklar)

            self.urunMarka.SetSelection(0)
            self.urunTur.SetSelection(0)
            self.urunAyrinti.SetSelection(0)
            self.urunAgirlik.SetSelection(0)

            self.markaYazi.Show()
            self.urunMarka.Show()
            self.ayrintiYazi.Show()
            self.urunAyrinti.Show()
            self.turYazi.Hide()
            self.urunTur.Hide()
            self.agirlikYazi.Show()
            self.urunAgirlik.Show()
            self.sorgula.Show()
        elif secim == 3:
            self.urunMarka.Clear()
            self.urunAyrinti.Clear()
            self.urunTur.Clear()
            self.urunAgirlik.Clear()

            markalar, digerAdlar, agirliklar = sorguIcinUrunBilgi(secim)

            self.urunMarka.Append(markalar)
            self.urunAyrinti.Append(digerAdlar)
            self.urunAgirlik.Append(agirliklar)

            self.urunMarka.SetSelection(0)
            self.urunTur.SetSelection(0)
            self.urunAyrinti.SetSelection(0)
            self.urunAgirlik.SetSelection(0)

            self.markaYazi.Show()
            self.urunMarka.Show()
            self.ayrintiYazi.Show()
            self.urunAyrinti.Show()
            self.turYazi.Hide()
            self.urunTur.Hide()
            self.agirlikYazi.Show()
            self.urunAgirlik.Show()
            self.sorgula.Show()
        elif secim == 4:
            self.urunMarka.Clear()
            self.urunAyrinti.Clear()
            self.urunTur.Clear()
            self.urunAgirlik.Clear()

            markalar, digerAdlar, agirliklar = sorguIcinUrunBilgi(secim)

            self.urunMarka.Append(markalar)
            self.urunAyrinti.Append(digerAdlar)
            self.urunAgirlik.Append(agirliklar)

            self.urunMarka.SetSelection(0)
            self.urunTur.SetSelection(0)
            self.urunAyrinti.SetSelection(0)
            self.urunAgirlik.SetSelection(0)

            self.markaYazi.Show()
            self.urunMarka.Show()
            self.ayrintiYazi.Show()
            self.urunAyrinti.Show()
            self.turYazi.Hide()
            self.urunTur.Hide()
            self.agirlikYazi.Show()
            self.urunAgirlik.Show()
            self.sorgula.Show()

    def urunBilgiGetir(self, olay):
        secim = self.urunlerinTuru.GetCurrentSelection()
        print(secim)
        if secim == 1:
            sorgu = 'select * from yagUrunleriT where yagAd='
            fiyatSorgu = 'select * from yagFiyatT'
            if self.urunMarka.GetValue() == 'Farketmez':
                marka = 'yagAd'
                sorgu = sorgu + marka
            else:
                marka = self.urunMarka.GetValue()
                sorgu = sorgu + '?'

            if self.urunAyrinti.GetValue() == 'Farketmez':
                ayrinti = 'yagDigerAd'
                sorgu = sorgu + ' and yagDigerAd='+ayrinti
            else:
                ayrinti = self.urunAyrinti.GetValue()
                sorgu = sorgu + ' and yagDigerAd=?'

            if self.urunTur.GetValue() == 'Farketmez':
                tur = 'yagTipi'
                sorgu = sorgu + ' and yagTipi='+tur
            else:
                tur = self.urunTur.GetValue()
                sorgu = sorgu + ' and yagTipi=?'

            if self.urunAgirlik.GetValue() == 'Farketmez':
                agirlik = 'yagAgirlik'
                sorgu = sorgu + ' and yagAgirlik='+agirlik
            else:
                agirlik = self.urunAgirlik.GetValue()
                sorgu = sorgu + ' and yagAgirlik=?'
            baglanti = veriTabaninaBaglan()
            if baglanti!=None:
                try:
                    imlec = baglanti.cursor()
                except Error as hata:
                    wx.MessageDialog(None, 'İmleç oluşturmada hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                else:
                    try:
                        if marka != 'yagAd' and ayrinti == 'yagDigerAd' and tur == 'yagTipi' and agirlik == 'yagAgirlik':
                            #imlec.execute('select * from yagUrunleriT where yagAd=? and yagDigerAd={ayr} and yagTipi={tip} and yagAgirlik={agi}'
                            #    .format(ad=marka, ayr=ayrinti, tip=tur, agi=agirlik), ([marka]))
                            #imlec.execute(sorgu,(ayrinti,tur,agirlik))
                            imlec.execute(sorgu, ([marka]))
                        elif marka == 'yagAd' and ayrinti != 'yagDigerAd' and tur == 'yagTipi' and agirlik == 'yagAgirlik':
                            imlec.execute(sorgu, ([ayrinti]))
                        elif marka == 'yagAd' and ayrinti == 'yagDigerAd' and tur != 'yagTipi' and agirlik == 'yagAgirlik':
                            imlec.execute(sorgu, ([tur]))
                        elif marka == 'yagAd' and ayrinti == 'yagDigerAd' and tur == 'yagTipi' and agirlik != 'yagAgirlik':
                            imlec.execute(sorgu, ([agirlik]))

                        elif marka != 'yagAd' and ayrinti != 'yagDigerAd' and tur == 'yagTipi' and agirlik == 'yagAgirlik':
                            imlec.execute(sorgu, (marka, ayrinti))
                        elif marka != 'yagAd' and ayrinti == 'yagDigerAd' and tur != 'yagTipi' and agirlik == 'yagAgirlik':
                            imlec.execute(sorgu, (marka, tur))
                        elif marka != 'yagAd' and ayrinti == 'yagDigerAd' and tur == 'yagTipi' and agirlik != 'yagAgirlik':
                            imlec.execute(sorgu, (marka, agirlik))

                        elif marka == 'yagAd' and ayrinti != 'yagDigerAd' and tur != 'yagTipi' and agirlik == 'yagAgirlik':
                            imlec.execute(sorgu, (ayrinti, tur))
                        elif marka == 'yagAd' and ayrinti != 'yagDigerAd' and tur == 'yagTipi' and agirlik != 'yagAgirlik':
                            imlec.execute(sorgu, (ayrinti, agirlik))

                        elif marka == 'yagAd' and ayrinti == 'yagDigerAd' and tur != 'yagTipi' and agirlik != 'yagAgirlik':
                            imlec.execute(sorgu, (tur, agirlik))

                        elif marka != 'yagAd' and ayrinti != 'yagDigerAd' and tur != 'yagTipi' and agirlik != 'yagAgirlik':
                            imlec.execute(sorgu, (marka, ayrinti, tur, agirlik))
                        elif marka == 'yagAd' and ayrinti == 'yagDigerAd' and tur == 'yagTipi' and agirlik == 'yagAgirlik':
                            imlec.execute(sorgu)
                    except Error as hata:
                        wx.MessageDialog(None, 'Sorgu çalışmadı.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    else:
                        urunler = imlec.fetchall()
                        try:
                            imlec.execute(fiyatSorgu)
                        except Error as hata:
                            wx.MessageDialog(None, 'Fiyat Sorgu çalışmadı.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                        else:
                            fiyatlar = imlec.fetchall()
                            """ for urun in urunler:
                                print(urun) """
                            veriCerceve = urunGoster(None, 'Yağ Ürünleri', 1024, 768, urunler, fiyatlar, 0)
                            veriCerceve.Show()
        elif secim == 2:
            sorgu = 'select * from icecekUrunleriT where icecekAd='
            fiyatSorgu = 'select * from icecekFiyatT'
            if self.urunMarka.GetValue() == 'Farketmez':
                marka = 'icecekAd'
                sorgu = sorgu + marka
            else:
                marka = self.urunMarka.GetValue()
                sorgu = sorgu + '?'

            if self.urunAyrinti.GetValue() == 'Farketmez':
                ayrinti = 'icecekDigerAd'
                sorgu = sorgu + ' and icecekDigerAd='+ayrinti
            else:
                ayrinti = self.urunAyrinti.GetValue()
                sorgu = sorgu + ' and icecekDigerAd=?'

            if self.urunAgirlik.GetValue() == 'Farketmez':
                agirlik = 'icecekAgirlik'
                sorgu = sorgu + ' and icecekAgirlik='+agirlik
            else:
                agirlik = self.urunAgirlik.GetValue()
                sorgu = sorgu + ' and icecekAgirlik=?'

            baglanti = veriTabaninaBaglan()
            if baglanti!=None:
                try:
                    imlec = baglanti.cursor()
                except Error as hata:
                    wx.MessageDialog(None, 'İmleç oluşturmada hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                else:
                    try:
                        if marka != 'icecekAd' and ayrinti == 'icecekDigerAd' and agirlik == 'icecekAgirlik':
                            #imlec.execute('select * from yagUrunleriT where yagAd=? and yagDigerAd={ayr} and yagTipi={tip} and yagAgirlik={agi}'
                            #    .format(ad=marka, ayr=ayrinti, tip=tur, agi=agirlik), ([marka]))
                            #imlec.execute(sorgu,(ayrinti,tur,agirlik))
                            imlec.execute(sorgu, ([marka]))
                        elif marka == 'icecekAd' and ayrinti != 'icecekDigerAd' and agirlik == 'icecekAgirlik':
                            imlec.execute(sorgu, ([ayrinti]))
                        elif marka == 'icecekAd' and ayrinti == 'icecekDigerAd'and agirlik != 'icecekAgirlik':
                            imlec.execute(sorgu, ([agirlik]))

                        elif marka != 'icecekAd' and ayrinti != 'icecekDigerAd' and agirlik == 'icecekAgirlik':
                            imlec.execute(sorgu, (marka, ayrinti))
                        elif marka != 'icecekAd' and ayrinti == 'icecekDigerAd' and agirlik != 'icecekAgirlik':
                            imlec.execute(sorgu, (marka, agirlik))
                        elif marka == 'icecekAd' and ayrinti != 'icecekDigerAd' and agirlik != 'icecekAgirlik':
                            imlec.execute(sorgu, (ayrinti, agirlik))

                        elif marka != 'icecekAd' and ayrinti != 'icecekDigerAd' and agirlik != 'icecekAgirlik':
                            imlec.execute(sorgu, (marka, ayrinti, agirlik))
                        elif marka == 'icecekAd' and ayrinti == 'icecekDigerAd' and agirlik == 'icecekAgirlik':
                            imlec.execute(sorgu)
                    except Error as hata:
                        wx.MessageDialog(None, 'Sorgu çalışmadı.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    else:
                        urunler = imlec.fetchall()
                        try:
                            imlec.execute(fiyatSorgu)
                        except Error as hata:
                            wx.MessageDialog(None, 'Fiyat Sorgu çalışmadı.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                        else:
                            fiyatlar = imlec.fetchall()
                            """ for urun in urunler:
                            print(urun) """
                            veriCerceve = urunGoster(None, 'İçecekler', 1024, 768, urunler, fiyatlar, 1)
                            veriCerceve.Show()
        elif secim == 3:
            sorgu = 'select * from peynirUrunleriT where peynirAd='
            fiyatSorgu = 'select * from peynirFiyatT'
            if self.urunMarka.GetValue() == 'Farketmez':
                marka = 'peynirAd'
                sorgu = sorgu + marka
            else:
                marka = self.urunMarka.GetValue()
                sorgu = sorgu + '?'

            if self.urunAyrinti.GetValue() == 'Farketmez':
                ayrinti = 'peynirDigerAd'
                sorgu = sorgu + ' and peynirDigerAd='+ayrinti
            else:
                ayrinti = self.urunAyrinti.GetValue()
                sorgu = sorgu + ' and peynirDigerAd=?'

            if self.urunAgirlik.GetValue() == 'Farketmez':
                agirlik = 'peynirAgirlik'
                sorgu = sorgu + ' and peynirAgirlik='+agirlik
            else:
                agirlik = self.urunAgirlik.GetValue()
                sorgu = sorgu + ' and peynirAgirlik=?'

            baglanti = veriTabaninaBaglan()
            if baglanti!=None:
                try:
                    imlec = baglanti.cursor()
                except Error as hata:
                    wx.MessageDialog(None, 'İmleç oluşturmada hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                else:
                    try:
                        if marka != 'peynirAd' and ayrinti == 'peynirDigerAd' and agirlik == 'peynirAgirlik':
                            #imlec.execute('select * from yagUrunleriT where yagAd=? and yagDigerAd={ayr} and yagTipi={tip} and yagAgirlik={agi}'
                            #    .format(ad=marka, ayr=ayrinti, tip=tur, agi=agirlik), ([marka]))
                            #imlec.execute(sorgu,(ayrinti,tur,agirlik))
                            imlec.execute(sorgu, ([marka]))
                        elif marka == 'peynirAd' and ayrinti != 'peynirDigerAd' and agirlik == 'peynirAgirlik':
                            imlec.execute(sorgu, ([ayrinti]))
                        elif marka == 'peynirAd' and ayrinti == 'peynirDigerAd'and agirlik != 'peynirAgirlik':
                            imlec.execute(sorgu, ([agirlik]))

                        elif marka != 'peynirAd' and ayrinti != 'peynirDigerAd' and agirlik == 'peynirAgirlik':
                            imlec.execute(sorgu, (marka, ayrinti))
                        elif marka != 'peynirAd' and ayrinti == 'peynirDigerAd' and agirlik != 'peynirAgirlik':
                            imlec.execute(sorgu, (marka, agirlik))
                        elif marka == 'peynirAd' and ayrinti != 'peynirDigerAd' and agirlik != 'peynirAgirlik':
                            imlec.execute(sorgu, (ayrinti, agirlik))

                        elif marka != 'peynirAd' and ayrinti != 'peynirDigerAd' and agirlik != 'peynirAgirlik':
                            imlec.execute(sorgu, (marka, ayrinti, agirlik))
                        elif marka == 'peynirAd' and ayrinti == 'peynirDigerAd' and agirlik == 'peynirAgirlik':
                            imlec.execute(sorgu)
                    except Error as hata:
                        wx.MessageDialog(None, 'Sorgu çalışmadı.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    else:
                        urunler = imlec.fetchall()
                        try:
                            imlec.execute(fiyatSorgu)
                        except Error as hata:
                            wx.MessageDialog(None, 'Fiyat Sorgu çalışmadı.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                        else:
                            fiyatlar = imlec.fetchall()
                            """ for urun in urunler:
                                print(urun) """
                            veriCerceve = urunGoster(None, 'Peynirler', 1024, 768, urunler, fiyatlar, 1)
                            veriCerceve.Show()
        elif secim == 4:
            sorgu = 'select * from makarnaUrunleriT where makarnaAd='
            fiyatSorgu = 'select * from makarnaFiyatT'
            if self.urunMarka.GetValue() == 'Farketmez':
                marka = 'makarnaAd'
                sorgu = sorgu + marka
            else:
                marka = self.urunMarka.GetValue()
                sorgu = sorgu + '?'

            if self.urunAyrinti.GetValue() == 'Farketmez':
                ayrinti = 'makarnaDigerAd'
                sorgu = sorgu + ' and makarnaDigerAd='+ayrinti
            else:
                ayrinti = self.urunAyrinti.GetValue()
                sorgu = sorgu + ' and makarnaDigerAd=?'

            if self.urunAgirlik.GetValue() == 'Farketmez':
                agirlik = 'makarnaAgirlik'
                sorgu = sorgu + ' and makarnaAgirlik='+agirlik
            else:
                agirlik = self.urunAgirlik.GetValue()
                sorgu = sorgu + ' and makarnaAgirlik=?'

            baglanti = veriTabaninaBaglan()
            if baglanti!=None:
                try:
                    imlec = baglanti.cursor()
                except Error as hata:
                    wx.MessageDialog(None, 'İmleç oluşturmada hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                else:
                    try:
                        if marka != 'makarnaAd' and ayrinti == 'makarnaDigerAd' and agirlik == 'makarnaAgirlik':
                            #imlec.execute('select * from yagUrunleriT where yagAd=? and yagDigerAd={ayr} and yagTipi={tip} and yagAgirlik={agi}'
                            #    .format(ad=marka, ayr=ayrinti, tip=tur, agi=agirlik), ([marka]))
                            #imlec.execute(sorgu,(ayrinti,tur,agirlik))
                            imlec.execute(sorgu, ([marka]))
                        elif marka == 'makarnaAd' and ayrinti != 'makarnaDigerAd' and agirlik == 'makarnaAgirlik':
                            imlec.execute(sorgu, ([ayrinti]))
                        elif marka == 'peynirAd' and ayrinti == 'makarnaDigerAd'and agirlik != 'makarnaAgirlik':
                            imlec.execute(sorgu, ([agirlik]))

                        elif marka != 'makarnaAd' and ayrinti != 'makarnaDigerAd' and agirlik == 'makarnaAgirlik':
                            imlec.execute(sorgu, (marka, ayrinti))
                        elif marka != 'makarnaAd' and ayrinti == 'makarnaDigerAd' and agirlik != 'makarnaAgirlik':
                            imlec.execute(sorgu, (marka, agirlik))
                        elif marka == 'makarnaAd' and ayrinti != 'makarnaDigerAd' and agirlik != 'makarnaAgirlik':
                            imlec.execute(sorgu, (ayrinti, agirlik))

                        elif marka != 'makarnaAd' and ayrinti != 'makarnaDigerAd' and agirlik != 'makarnaAgirlik':
                            imlec.execute(sorgu, (marka, ayrinti, agirlik))
                        elif marka == 'makarnaAd' and ayrinti == 'makarnaDigerAd' and agirlik == 'makarnaAgirlik':
                            imlec.execute(sorgu)
                    except Error as hata:
                        wx.MessageDialog(None, 'Sorgu çalışmadı.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    else:
                        urunler = imlec.fetchall()
                        try:
                            imlec.execute(fiyatSorgu)
                        except Error as hata:
                            wx.MessageDialog(None, 'Fiyat Sorgu çalışmadı.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                        else:
                            fiyatlar = imlec.fetchall()
                            """ for urun in urunler:
                                print(urun) """
                            veriCerceve = urunGoster(None, 'Makarnalar', 1024, 768, urunler, fiyatlar, 1)
                            veriCerceve.Show()
        
    def getirilecekBilgi(self, olay, kutu):
        self.siviYagBilgi.Show()
        self.icecekgBilgi.Show()
        self.peynirBilgi.Show()
        self.makarnaBilgi.Show()
        #self.toptanBilgi.Show()
        self.gizleBilgi.Show()

    ##############################---BİLGİLERİ İNTERNET SİTESİNDEN ALMA (AŞAĞISI)---##############################
    def yagBilgiGetir(self,olay):
        self.siviYagBilgi.Hide()
        self.icecekgBilgi.Hide()
        self.peynirBilgi.Hide()
        self.makarnaBilgi.Hide()
        #self.toptanBilgi.Hide()
        self.gizleBilgi.Hide()
        onay = urunlerinBilgileriniGetir(0)
        if onay != 0:
            olduMu = basariliMi()
            if olduMu != 0:
                eklensinMi = wx.MessageDialog(None, 'Çekilen verileri veri tabanına eklemek ister misiniz?', 'Onay', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION).ShowModal()
                if eklensinMi == wx.ID_YES:
                    try:
                        urunleriVtEkle(0)
                    except:
                        wx.MessageDialog(None, 'Verileri eklemede hata oldu!','HATA', wx.OK|wx.ICON_ERROR).ShowModal()
        else:
            wx.MessageDialog(None, 'Veriler internetten alınamadı','HATA', wx.OK|wx.ICON_ERROR).ShowModal()
    
    def icecekBilgiGetir(self, olay):
        self.siviYagBilgi.Hide()
        self.icecekgBilgi.Hide()
        self.peynirBilgi.Hide()
        self.makarnaBilgi.Hide()
        #self.toptanBilgi.Hide()
        self.gizleBilgi.Hide()
        onay = urunlerinBilgileriniGetir(1)
        if onay != 0:
            olduMu = basariliMi()
            if olduMu != 0:
                eklensinMi = wx.MessageDialog(None, 'Çekilen verileri veri tabanına eklemek ister misiniz?', 'Onay', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION).ShowModal()
                if eklensinMi == wx.ID_YES:
                    try:
                        urunleriVtEkle(1)
                    except:
                        wx.MessageDialog(None, 'Verileri eklemede hata oldu!','HATA', wx.OK|wx.ICON_ERROR).ShowModal()

    def peynirBilgiGetir(self, olay):
        self.siviYagBilgi.Hide()
        self.icecekgBilgi.Hide()
        self.peynirBilgi.Hide()
        self.makarnaBilgi.Hide()
        #self.toptanBilgi.Hide()
        self.gizleBilgi.Hide()
        onay = urunlerinBilgileriniGetir(2)
        if onay != 0:
            olduMu = basariliMi()
            if olduMu != 0:
                eklensinMi = wx.MessageDialog(None, 'Çekilen verileri veri tabanına eklemek ister misiniz?', 'Onay', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION).ShowModal()
                if eklensinMi == wx.ID_YES:
                    try:
                        urunleriVtEkle(2)
                    except:
                        wx.MessageDialog(None, 'Verileri eklemede hata oldu!','HATA', wx.OK|wx.ICON_ERROR).ShowModal()

    def makarnaBilgiGetir(self, olay):
        self.siviYagBilgi.Hide()
        self.icecekgBilgi.Hide()
        self.peynirBilgi.Hide()
        self.makarnaBilgi.Hide()
        #self.toptanBilgi.Hide()
        self.gizleBilgi.Hide()
        onay = urunlerinBilgileriniGetir(3)
        if onay != 0:
            olduMu = basariliMi()
            if olduMu != 0:
                eklensinMi = wx.MessageDialog(None, 'Çekilen verileri veri tabanına eklemek ister misiniz?', 'Onay', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION).ShowModal()
                if eklensinMi == wx.ID_YES:
                    try:
                        urunleriVtEkle(3)
                    except:
                        wx.MessageDialog(None, 'Verileri eklemede hata oldu!','HATA', wx.OK|wx.ICON_ERROR).ShowModal()

    def toptanBilgiGetir(self, olay):
        self.siviYagBilgi.Hide()
        self.icecekgBilgi.Hide()
        self.peynirBilgi.Hide()
        self.makarnaBilgi.Hide()
        #self.toptanBilgi.Hide()
        self.gizleBilgi.Hide()
        onay = urunlerinBilgileriniGetir(4)
        if onay != 0:
            olduMu = basariliMi()
            if olduMu != 0:
                eklensinMi = wx.MessageDialog(None, 'Çekilen verileri veri tabanına eklemek ister misiniz?', 'Onay', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION).ShowModal()
                if eklensinMi == wx.ID_YES:
                    try:
                        urunleriVtEkle(4)
                    except:
                        wx.MessageDialog(None, 'Verileri eklemede hata oldu!','HATA', wx.OK|wx.ICON_ERROR).ShowModal()
    
    def gizleBilgiGetir(self, olay):
        self.siviYagBilgi.Hide()
        self.icecekgBilgi.Hide()
        self.peynirBilgi.Hide()
        self.makarnaBilgi.Hide()
        #self.toptanBilgi.Hide()
        self.gizleBilgi.Hide()
    ##############################---BİLGİLERİ İNTERNET SİTESİNDEN ALMA (YUKARISI)---##############################


    def yagGetir(self, olay, kutu):
        aramaKomutu = '''select * from yagUrunleriT'''
        fiyatArama = '''select * from yagFiyatT'''
        baglanti = veriTabaninaBaglan()
        if baglanti != None:
            try:
                imlec = baglanti.cursor()
            except Error as hata:
                wx.MessageDialog(None, 'İmleç oluşturmada hata oldu(Ürün Gösterme).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                return 0
            else:
                try:
                    imlec.execute(aramaKomutu)
                except Error as hata:
                    wx.MessageDialog(None, 'Ürünleri veri tabanından çekmede hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    return 0
                else:
                    urunler = imlec.fetchall()
                    try:
                        imlec.execute(fiyatArama)
                    except Error as hata:
                        wx.MessageDialog(None, 'Ürünleri veri tabanından çekmede hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                        return 0
                    else:
                        fiyatlar = imlec.fetchall()
                        veriCerceve = urunGoster(None, 'Yağ Ürünleri', 1024, 768, urunler, fiyatlar, 0)
                        veriCerceve.Show()
                
    def icecekGetir(self, olay, kutu):
        aramaKomutu = '''select * from icecekUrunleriT'''
        fiyatArama = '''select * from icecekFiyatT'''
        baglanti = veriTabaninaBaglan()
        if baglanti != None:
            try:
                imlec = baglanti.cursor()
            except Error as hata:
                wx.MessageDialog(None, 'İmleç oluşturmada hata oldu(Ürün Gösterme).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                return 0
            else:
                try:
                    imlec.execute(aramaKomutu)
                except Error as hata:
                    wx.MessageDialog(None, 'Ürünleri veri tabanından çekmede hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    return 0
                else:
                    urunler = imlec.fetchall()
                    try:
                        imlec.execute(fiyatArama)
                    except Error as hata:
                        wx.MessageDialog(None, 'Ürünleri veri tabanından çekmede hata oldu.\n\tHata: ' + str(
                            hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                        return 0
                    else:
                        fiyatlar = imlec.fetchall()
                        veriCerceve = urunGoster(None, 'İçecekler', 1024, 768, urunler, fiyatlar, 1)
                        veriCerceve.Show()

    def peynirGetir(self, olay, kutu):
        aramaKomutu = '''select * from peynirUrunleriT'''
        fiyatArama = '''select * from peynirFiyatT'''
        baglanti = veriTabaninaBaglan()
        if baglanti != None:
            try:
                imlec = baglanti.cursor()
            except Error as hata:
                wx.MessageDialog(None, 'İmleç oluşturmada hata oldu(Ürün Gösterme).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                return 0
            else:
                try:
                    imlec.execute(aramaKomutu)
                except Error as hata:
                    wx.MessageDialog(None, 'Ürünleri veri tabanından çekmede hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    return 0
                else:
                    urunler = imlec.fetchall()
                    try:
                        imlec.execute(fiyatArama)
                    except Error as hata:
                        wx.MessageDialog(None, 'Ürünleri veri tabanından çekmede hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                        return 0
                    else:
                        fiyatlar = imlec.fetchall()
                        veriCerceve = urunGoster(None, 'Peynirler', 1024, 768, urunler, fiyatlar, 2)
                        veriCerceve.Show()

    def makarnaGetir(self, olay, kutu):
        aramaKomutu = '''select * from makarnaUrunleriT'''
        fiyatArama = '''select * from makarnaFiyatT'''
        baglanti = veriTabaninaBaglan()
        if baglanti != None:
            try:
                imlec = baglanti.cursor()
            except Error as hata:
                wx.MessageDialog(None, 'İmleç oluşturmada hata oldu(Ürün Gösterme).\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                return 0
            else:
                try:
                    imlec.execute(aramaKomutu)
                except Error as hata:
                    wx.MessageDialog(None, 'Ürünleri veri tabanından çekmede hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                    return 0
                else:
                    urunler = imlec.fetchall()
                    try:
                        imlec.execute(fiyatArama)
                    except Error as hata:
                        wx.MessageDialog(None, 'Ürünleri veri tabanından çekmede hata oldu.\n\tHata: ' + str(hata), 'HATA!', wx.OK | wx.ICON_ERROR).ShowModal()
                        return 0
                    else:
                        fiyatlar = imlec.fetchall()
                        veriCerceve = urunGoster(None, 'Makarnalar', 1024, 768, urunler, fiyatlar, 3)
                        veriCerceve.Show()
#############################################################
###################---BAŞLANGIÇ---###################
def kullaniciArayuzu():
    uygulama = wx.App()
    cerceve = anaPencere(None, 'Veri Görsellerini Görüntüle', 1024, 768)
    cerceve.Show()
    uygulama.MainLoop()


def ana():
    kullaniciArayuzu()

#####################################################
if __name__ == '__main__':
    ana()
