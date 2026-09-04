# Pergamino Precios - APK

App Android sencilla y amigable para comparar precios en MasOnline, VEA y Carrefour (Pergamino).

## Features
- **Comparar precios**: Buscá "coca cola 2.25", "leche serenisima", etc. Muestra precio regular, precio efectivo c/u con promo (2x1, 3x2, 2do 50%), y link a tienda.
- **Más barato inteligente**: Indica más barato x1 y más barato llevando promo (ej: $4.425 c/u llevando 2 en Carrefour).
- **Promos Bancarias**: Apartado dedicado por supermercado (MasOnline, VEA, Carrefour) con promos de pago detectadas dinámicamente (Cencopay, CSI, cuotas, bancos) + estáticas.

## Probar en PC (Windows)
```bash
pip install kivy kivymd requests
python main.py
```

## Compilar APK (requiere Linux/WSL)
### Opción A: GitHub Actions (recomendado)
1. Push a GitHub (rama dev/main)
2. Actions → Build APK → Run workflow → Descargar artifact

### Opción B: WSL
```bash
sudo apt install -y python3-pip openjdk-17-jdk zip unzip
pip install buildozer cython==0.29.33
cd pycom/app
buildozer android debug
```
