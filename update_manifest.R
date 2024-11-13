### AFD Comment - Command R a executer directement depuis le terminal shell : < Rscript update_manifest.R > ###
### AFD Comment - Au besoin, adapter le script su la base du fichier (version et autres) douvent être modifier ###
# Installer les packages nécessaires si ce n'est pas déjà fait
if (!require(jsonlite)) install.packages("jsonlite")
if (!require(digest)) install.packages("digest")
if (!require(fs)) install.packages("fs")

# Charger les packages
library(jsonlite)
library(digest)
library(fs)

# Fonction pour mettre à jour le fichier manifest.json
update_manifest <- function(manifest_path = "manifest.json") {
  # Lire le fichier manifest.json existant s'il existe
  if (file.exists(manifest_path)) {
    manifest <- fromJSON(manifest_path)
  } else {
    # Créer un nouveau manifest s'il n'existe pas
    manifest <- list(
      version = 1,
      metadata = list(
        appmode = "python-streamlit",
        entrypoint = "app"
      ),
      python = list(
        version = "3.8.6",
        package_manager = list(
          name = "pip",
          version = "23.0.1",
          package_file = "requirements.txt"
        )
      ),
      files = list()
    )
  }
  
  # Parcourir les fichiers dans le répertoire actuel et ses sous-répertoires
  files <- dir_ls(recurse = TRUE, full.names = TRUE)
  
  # Créer une liste pour les checksums
  checksums <- list()
  
  # Calculer les checksums des fichiers et mettre à jour la liste
  for (file in files) {
    if (file_test("-f", file)) {  # Vérifier si le fichier est un fichier régulier
      # Lire le contenu du fichier
      file_content <- readBin(file, what = "raw", n = file.size(file))
      # Calculer le checksum
      checksum <- digest(file_content, algo = "md5", serialize = FALSE)
      # Ajouter le checksum à la liste
      checksums[[file]] <- list(checksum = checksum)
    }
  }
  
  # Mettre à jour la section files du manifest
  manifest$files <- checksums
  
  # Écrire le manifest mis à jour dans le fichier
  write_json(manifest, path = manifest_path, pretty = TRUE, auto_unbox = TRUE)
  
  cat("Le fichier manifest.json a été mis à jour avec succès.\n")
}

# Exécuter la fonction pour mettre à jour le manifest
update_manifest()