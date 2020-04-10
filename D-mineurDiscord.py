
# Importation des modules
import numpy as np
from scipy import signal
import discord


client = discord.Client()

with open("token.txt","r") as f:
    token = f.readline().replace("\n","")


# Variables

longueur = 10
hauteur = 10
pourcentageMines = 12
comparaison = np.ones((3, 3), dtype=int)
comparaison[1, 1] = 0
affichage_mine = " M "
logo = {0: "⬛", 1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣",
        5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣", 10: "🔟"}
win = False
loose = False
joueur = ""
partie = False
liste_parties = {}
texte_aide = ("Démineur développé entièrement par Marius ROBERT\n\n"
            "`+dm new partie` pour commencer une nouvelle partie avec le nom partie\n"
            "`+dm dig partie x y` pour creuser en x y dans la partie partie (coordonnées x en haut et y à gauche)\n"
            "si vous creusez une case déjà creusée avec le nombre de drapeaux correspondants sont placés autour, les 8 cases autour sont creusés (excepté les drapeaux)\n"
            "`+dm flag partie x y` pour poser/retirer un drapeau en x y dans la partie partie, une case ne peut pas être creusée si un drapeau y est plac\n"
            "`+dm cancel partie` pour arreter la partie partie\n"
            "`+dm add partie @joueur#0000` pour autoriser @joueur#0000 à jouer, supprimer et autoriser d'autres personnes dans la partie\n"
            "`+dm help` pour afficher ce message\n"
            "Une fois que la partie est gagnée ou perdue, elle est automatiquement effacée")


# Classes

class Game():
    def __init__(self, nom, joueur, hauteur=10, longueur=10, pourcentageMines=10):
        self.nom = nom
        self.hauteur = hauteur
        self.longueur = longueur
        self.joueurs = [joueur]

        self.map_jeu = np.zeros((hauteur, longueur))
        self.map_inconnue = np.ones((hauteur, longueur), dtype=int)
        self.map_mines = np.zeros((hauteur, longueur), dtype=int)
        self.map_affiche = np.zeros((hauteur, longueur), dtype=int)
        self.map_affiche = np.where(self.map_affiche == 0, "🟦", self.map_affiche)
        self.map_jeu = (np.random.randint(0, 100, (hauteur, longueur)) <= pourcentageMines).astype(int)
        self.map_compteur = signal.convolve2d(self.map_jeu, comparaison, mode="same", boundary="fill")
        self.loose = False
        self.win = False


    def check_win(self):
        if np.sum(self.map_inconnue != self.map_jeu) == 0 or np.sum(self.map_jeu != self.map_mines) == 0:
            self.win = True


    def click(self, y, x):
        if self.map_jeu[y, x] == 1 and self.map_affiche[y, x] == "🟦":
            self.loose = True
            self.map_affiche[y, x] = "❌"

        elif self.map_affiche[y, x] == "🚩":
            pass

        elif self.map_affiche[y, x] == "🟦":
            self.map_affiche[y, x] = logo.get(self.map_compteur[y, x])
            self.map_inconnue[y, x] = 0

            if self.map_affiche[y, x] == "⬛":
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        if y + i >= 0 and x + j >= 0:
                            try:
                                self.click(y + i, x + j)
                            except IndexError:
                                pass

        elif self.map_affiche[y, x] in logo.values() and self.map_affiche[y, x] != "⬛":
            self.double_click(y, x)


        self.check_win()


    def drapeau(self, y, x):
        if self.map_affiche[y, x] == "🟦":
            self.map_affiche[y, x] = "🚩"
            self.map_mines[y, x] = 1

        elif self.map_affiche[y, x] == "🚩":
            self.map_affiche[y, x] = "🟦"
            self.map_mines[y, x] = 0

        self.check_win()

    def double_click(self, y, x):
        if self.map_affiche[y, x] == logo.get(signal.convolve2d(self.map_mines, comparaison, mode="same", boundary="fill")[y, x]):
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if y+i >= 0 and x+j >= 0 and y+i < self.hauteur and x+j < self.longueur:
                        self.click(y + i, x + j)




async def affiche_game(channel, game):
    texte_jeu = ""
    for i in range(game.longueur+1):
        texte_jeu += logo.get(i)
    texte_jeu += "\n"+logo.get(1)
    for ligne in range(game.hauteur):
        for colonne in range(game.longueur):
            texte_jeu += str(game.map_affiche[ligne, colonne])
        if ligne != np.shape(game.map_affiche)[0]-1:
            texte_jeu += "\n"
            texte_jeu += str(logo.get(ligne+2))

    if game.loose == True:
        texte_jeu += "\nPerdu, vous êtes nul !"
        del liste_parties[game.nom]

    if game.win == True:
        texte_jeu += "\nBravo, vous avez gagné"
        del liste_parties[game.nom]

    await send_message(channel, texte_jeu)


async def send_message(channel, message):
    await channel.send(message)




def analyse_commande(message):
    message_split = message.content.split()

    try:
        nom_game = message_split[2]
    except IndexError:
        return "erreur_format", "Veuillez spécifier un nom de partie"
    try:
        game = liste_parties[nom_game]
    except:
        return "erreur_format", "La partie `{}` n'existe pas".format(nom_game)

    if not message.author.mention in game.joueurs:
        return "erreur_format", "Nous n'êtes pas autorisé à effectuer cette action sur cette partie"
    try:
        x = -1
        x = int(message_split[3]) - 1
    except IndexError:
        return "erreur_format",  "Veuillez spécifier des coordonnées X"
    try:
        y = -1
        y = int(message_split[4]) - 1
    except IndexError:
        return "erreur_format", "Veuillez spécifier des coordonnées Y"

    if x < game.longueur and x >= 0:
        if y < game.hauteur and y >= 0:
            return game, x,y
        else:
            return "erreur_format", "Valeur Y incorrecte"
    else:
        if y < game.hauteur and y >= 0:
            return "erreur_format", "Valeur X incorrecte"
        else:
            return "erreur_format", "Valeurs X et Y incorrectes"


# Commandes Discord

@client.event
async def on_message(message):
    if message.author == client.user:
        print("non1")
        return
    if message.author.bot:
        print("non2")
        return

    message_split = message.content.split()
    print (message_split)
    if len(message_split) < 2:
        print("non3")
        return
    if message_split[0] != "+dm":
        print("non4")
        return

    if message_split[1] == "new":
        error = False
        try:
            nom_game = message_split[2]
        except IndexError:
            error = True
            await send_message(message.channel, "Veuillez spécifier un nom de partie")

        try:
            liste_parties[nom_game]
            error = True
            await send_message(message.channel, "Nom de partie déjà utilisé")
        except:
            pass

        if not error:
            liste_parties[nom_game] = Game(nom=nom_game, joueur=message.author.mention)
            await affiche_game(message.channel, liste_parties[nom_game])
            await send_message(message.channel, "Partie `{}` crée".format(nom_game))

    elif message_split[1] == "dig" or message_split[1] == "d":
        print('in dig')
        analyse = analyse_commande(message)
        print(analyse)
        if analyse[0] == "erreur_format":
            await send_message(message.channel, analyse[1])
        else:
            analyse[0].click(analyse[1], analyse[2])
            await affiche_game(message.channel, analyse[0])

    elif message_split[1] == "flag" or message_split[1] == "f":
        analyse = analyse_commande(message)
        if analyse[0] == "erreur_format":
            await send_message(message.channel, analyse[1])
        else:
            analyse[0].drapeau(analyse[1], analyse[2])
            await affiche_game(message.channel, analyse[0])

    elif message_split[1] == "add":
        try:
            nom_game = message_split[2]
        except IndexError:
            await send_message(message.channel, "Veuillez spécifier un nom de partie")
            error = True

        try:
            game = liste_parties[nom_game]
        except:
            await send_message(message.channel, "La partie `{}` n'existe pas".format(nom_game))
            error = True

        if not error:
            if message.author.mention in game.joueurs:
                game.joueurs.append(message.mentions[0].mention)
                await send_message(message.channel, "{} a désormais accès aux commandes de la partie `{}`".format(message.mentions[0].mention, nom_game))
            else:
                await send_message(message.channel, "Vous n'êtes pas autorisé à effectuer cette action sur cette partie")

    elif message_split[1] == "help":
        await send_message(message.channel, texte_aide)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await client.change_presence(activity=discord.Game(name='Minesweeper Windows XP'))

client.run(token)

#
