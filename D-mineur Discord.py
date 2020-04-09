
# Importation des modules
import numpy as np
from scipy import signal
import discord
from discord.ext import tasks

client = discord.Client(status="Démineur")

# Variables

longueur = 10
hauteur = 10
pourcentageMines = 12
comparaison = np.ones((3, 3), dtype=int)
comparaison[1, 1] = 0
affichage_mine = " M "
logo = {0:"⬛", 1:"1️⃣", 2:"2️⃣", 3:"3️⃣", 4:"4️⃣",
        5:"5️⃣", 6:"6️⃣", 7:"7️⃣", 8:"8️⃣", 9:"9️⃣", 10:"🔟"}
victoire = False
loose = False
joueur = ""
partie = False
texte_aide = ("Démineur développé entièrement par Marius ROBERT\n\""
            "+dm new\" pour commencer une nouvelle partie\n\""
            "+dm digx x sont placés autour y\" pour creuser en x y (coordonnées x en haut et y à gauche)\n"
            "si vous creusez une case déjà creusée avec le nombre de drapeaux correspondants sont placés autour, les 8 cases autour sont creusés (excepté les drapeaux)\n\""
            "+dm flag x y\" pour poser/retirer un drapeau en x y, une case ne peut pas être creusée si un drapeau y est plac\n\""
            "+dm cancel\" pour arreter une partie\n\"+dm help\" pour afficher ce message")

#Création de la map_jeu et de celle a afficher lors du clic




# Fonctions

def check_win():
    global victoire
    if np.sum(map_connue!=map_jeu) == 0 or np.sum(map_jeu!=map_mines) == 0:
        victoire = True
        print("Gagné")



#Affichage de la map_jeu
def initialisation(longueur, hauteur):
    global map_affiche, map_connue, map_mines, map_jeu, map_compteur
    map_jeu = np.zeros((hauteur, longueur))
    map_connue = np.ones((hauteur, longueur), dtype=int)
    map_mines = np.zeros((hauteur, longueur), dtype=int)
    map_affiche = np.zeros((hauteur, longueur), dtype=int)
    map_affiche = np.where(map_affiche==0, "🟦", map_affiche)
    map_jeu = (np.random.randint(0, 100, (hauteur, longueur)) <= pourcentageMines).astype(int)
    map_compteur = signal.convolve2d(map_jeu, comparaison, mode="same", boundary="fill")



#Event souris

def click(y, x):
    global map_affiche, loose
    if map_jeu[y, x] == 1 and map_affiche[y, x] == "🟦":
        print("Perdu")
        loose = True
        map_affiche[y, x] = "❌"

    else:
        if map_affiche[y, x] == "🟦":
            map_affiche[y, x] = logo.get(map_compteur[y, x])
            map_connue[y, x] = 0
            try:
                if map_affiche[y, x] == "⬛":
                    for i in range(-1, 2):
                        for j in range(-1, 2):
                            if y+i>=0 and x+j>=0:
                                click(y+i, x+j)
            except IndexError:
                pass

    check_win()

def drapeau(y, x):
    global map_affiche
    if map_affiche[y, x] == "🟦":
        map_affiche[y, x] = "🚩"
        map_mines[y, x] = 1

    elif map_affiche[y, x] == "🚩":
        map_affiche[y, x] = "🟦"
        map_mines[y, x] = 0

    check_win()

def double_click(y, x):
    global map_affiche
    print(signal.convolve2d(map_mines, comparaison, mode="same", boundary="fill")[y, x])
    print(logo.get(signal.convolve2d(map_mines, comparaison, mode="same", boundary="fill")[y, x]))

    if map_affiche[y, x] == logo.get(signal.convolve2d(map_mines, comparaison, mode="same", boundary="fill")[y, x]):
        for i in range(-1, 2):
            for j in range(-1, 2):
                if y+i>=0 and x+j>=0:
                    click(y+i, x+j)


initialisation(longueur, hauteur)


async def affiche_game(channel):
    global joueur, victoire, loose, partie

    texte_jeu = "🔲1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣8️⃣9️⃣🔟\n1️⃣"
    for ligne in range(np.shape(map_affiche)[0]):
        for case in range(np.shape(map_affiche)[0]):
            texte_jeu += str(map_affiche[ligne, case])
        if ligne != np.shape(map_affiche)[0]-1:
            texte_jeu += "\n"
            texte_jeu += str(logo.get(ligne+2))

    if loose == True:
        texte_jeu += "\nPerdu, vous aurez peut-être plus de chance la prochaine fois"
        joueur = ""
        partie = False
        loose = False

    elif victoire == True:
        texte_jeu += "\nBien joué, vous avez gagné"
        joueur = ""
        partie = False
        victoire = False

    await channel.send(texte_jeu)


async def affiche_erreur(channel, erreur):
    if erreur == "mauvais joueur":
        await channel.send("Une partie est déjà en cours et ce n'est pas la tienne, attend que l'autre partie soit finie pour en commencer une autre")
    elif erreur == "déjà partie":
        await channel.send("Vous êtes déjà en partie, finissez-là ou faites +dm cancel pour arreter")
    elif erreur == "pas partie":
        await channel.send("Vous devez d'abord créer une partie avec +dm new pour jouer")

@client.event
async def on_message(message):
    global joueur, partie

    if message.author.bot:
        pass
    message_split = message.content.split()
    print(message_split)
    print(message.author.id)
    print(joueur)
    if message_split[0] == "+dm":
        print(victoire)
        if joueur == "" or message.author.id == joueur:
            if message_split[1] == "new":
                if partie == False:
                    partie = True
                    initialisation(longueur, hauteur)
                    joueur = message.author.id
                    await affiche_game(message.channel)
                else:
                    await affiche_erreur(message.channel, "déjà partie")

            elif message_split[1] == "cancel":
                if partie == False:
                    await message.channel.send("Aucune partie à arreter")
                else:
                    partie = False
                    joueur = ""
                    await message.channel.send("Partie annulée")


            elif message_split[1] == "dig":
                if partie == False:
                    await affiche_erreur(message.channel, "pas partie")
                else:
                    coords = [int(message_split[3])-1, int(message_split[2])-1]
                    print(coords)
                    if map_affiche[coords[0], coords[1]] == "🟦":
                        click(coords[0], coords[1])
                    else:
                        double_click(coords[0], coords[1])
                    await affiche_game(message.channel)

            elif message_split[1] == "flag":
                if partie == False:
                    await affiche_erreur(message.channel, "pas partie")
                else:
                    coords = [int(message_split[3])-1, int(message_split[2])-1]
                    drapeau(coords[0], coords[1])
                    await affiche_game(message.channel)

            elif message_split[1] == "help":
                await message.channel.send(texte_aide)

        else:
            await affiche_erreur(message.channel, "mauvais joueur")





@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run("Njk3Mzc1NDExMDAwMDQ5NzE1.Xo3HkQ.-bpvsDtJxpDB5dVk4d8Wak6wuAI")
#
