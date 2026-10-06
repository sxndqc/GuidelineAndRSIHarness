kmerror.keymissing <- 
    paste("No API key specified. Specify apikey via mp_setapikey()",
          "or go to https://manifesto-project.wzb.eu to create key and/or",
          "account.")

#' Set the API key for the Manifesto Documents Database.
#' 
#' If you do not have an API key for the Manifesto Documents Database,
#' you can create one via your profile page on 
#' \url{https://manifesto-project.wzb.eu}.
#' If you do not have an account, you can register on the webpage.
#' 
#' The key is read from the file specified in \code{key.file}. If this
#' argument is \code{NULL}, the key given in the argument \code{key} is used.  
#'
#' @param key new API key
#' @param key.file file name containing the API key
#' @export
mp_setapikey <- function(key.file = NULL, key = NA_character_) {
  if (!is.null(key.file)) {
    tryCatch({
      fl <- file(key.file)
      key <- readLines(fl, 1, warn = FALSE)      
      # check key?
    }, finally = { close.connection(fl)})
  }
  assign(kapikey, key, envir = mp_globalenv)
}
mp_setapikey(key = NA_character_)

seturlapiroot <- function(apiroot) {
  if (grepl("^(https://([^/\\.]*\\.)*manifesto-project\\.wzb\\.eu|https*://(localhost|127.0.0.1)(:[0-9]+)*)/", apiroot)) {
    assign(kurlapiroot, apiroot, envir = mp_globalenv)
  } else {
    stop("please provide valid value for the api root url")
  }
}
seturlapiroot("https://manifesto-project.wzb.eu/api/v1/")

seturloriginalsroot <- function(originalsroot) {
  if (grepl("^(https://([^/\\.]*\\.)*manifesto-project\\.wzb\\.eu|https*://(localhost|127.0.0.1)(:[0-9]+)*)/", originalsroot)) {
    assign(kurloriginalsroot, originalsroot, envir = mp_globalenv)
  } else {
    stop("please provide valid value for originals root url")
  }
}
seturloriginalsroot("https://manifesto-project.wzb.eu/")

toamplist <- function(params) {
  pairs <- paste(names(params), params, sep="=")
  return(Reduce(function(x, y){ paste(x, y, sep="&") }, pairs))
}

formatmetaparams <- function(ids) {
  
  ids <- paste(ids$party, ids$date, sep="_")
  parameters <- as.list(ids)
  names(parameters) <- rep("keys[]", length(parameters))
  
  return(parameters)
  
}

formattextparams <- function(ids, additional_parameters = list()) {
  
  parameters <- as.list(ids$manifesto_id)
  names(parameters) <- rep("keys[]", length(parameters))
  
  return(c(parameters, additional_parameters))
  
}

separate_missings <- function(robj, request="") {
  
  missings <- robj$missing_items

  robj <- robj$items

  for (misskey in missings) {
    
    if (request %in% c("metadata", "text")) {
      
      warning(paste0("No document/metadata found with id ", misskey, ". ",
                     "Please double check your request if it was specified manually."),
              call. = FALSE)
      
    } else {
      
      warning(paste0("No information returned from API for key ", misskey))
      
    }
  }
  
  
  return(robj)
}


#' Format the main data set
#' 
#' Creates the format that is visible to the R user
#' from the internal data.frames files (in cache or from the API)
#'
#' @param mpds A data.frame with a main data set version to be formatted
formatmpds <- function(mpds) {
    
  # fix names
  names(mpds) <- tolower(make.names(as.vector(as.matrix(mpds[1,])))) 
  mpds <- mpds[-1,] # names are in first row
  row.names(mpds) <- NULL # or: paste(mpds$party, mpds$date, sep="-")  

  for (name in names(mpds)) {

    if (!name %in% c("edate", "countryname", "partyname", "candidatename", "partyabbrev", "datasetversion", "id_perm", "corpusversion")) {
      mpds[,name] <- as.numeric(recode(as.character(mpds[,name]), "NA" = NA_character_))
    }

    if (name == "edate") {
      mpds[,name] <- as.Date(as.character(mpds[,name]), format="%d/%m/%Y")
    }

  }

  return(mpds)

}

#' Format the parties data set
#'
#' Creates the format that is visible to the R user
#' from the internal data.frames files (in cache or from the API)
#'
#' @param partiesds A data.frame with a parties dataset to be formatted
formatpartiesds <- function(partiesds) {
  for (name in names(partiesds)) {
    if (name %in% c("country", "party", "year_min", "year_max", "max_pervote", "max_presvote", "year_max_pervote", "year_max_presvote",
                    "change_rank", "change_year_min", "change_year_max", "is_alliance")) {
      partiesds[, name] <- as.numeric(recode(as.character(partiesds[[name]]), "NA" = NA_character_))
    }
  }
  return(partiesds)
}

#' Manifesto Project DB API request
#' 
#' gets the requested url and passes HTTP header error codes on to raise R
#' errors with the same text
#'
#' @param file file to request below apiroot url
#' @param body body text of the posted request: should contain the parameters
#'             as specified by the Manifesto Project Database API
#' @param apikey API key to use, defaults to \code{NULL}, which means no key 
#'               is provided
mpdb_api_request <- function(file, body, apikey = NULL) {

  additional_headers <- if (!is.null(apikey)) {
    httr::add_headers(Authorization = paste0("Token ", apikey))
  } else {
    list()
  }
  response <- httr::POST(url=paste0(get(kurlapiroot, envir = mp_globalenv), file),
                         body=body,
                         config = additional_headers,
                         httr::user_agent(paste("httr",
                                                utils::packageVersion("httr"),
                                                "manifestoR",
                                                utils::packageVersion("manifestoR"))),
                         httr::config(followlocation = 0L))
  while (response$status_code %in% c(301:303)) { ## Manual following of redirects
    response <- httr::GET(response$headers$location)
  }
  content <- httr::content(response, as="text")
  if (response$status_code != "200") {
    msg <- paste("HTTP Error", response$status_code,
                 "when connecting to Manifesto Corpus Database")
    try({
      msg <- paste0(msg, ": ", fromJSON(content)$error, ".")
    }, silent = TRUE)
    if (response$status_code == 401) {
      msg <- paste(msg, "This can indicate an invalid API key.")
    }
    if (response$status_code == 404) {
      msg <- paste(msg, "This can indicate that you are requesting a version,",
                   "document, ... that does not exist. Please double check",
                   "your query parameters.")
    }
    stop(msg, call. = FALSE)
  } else {
    return(content[1])
  }
}

#' Download content from the Manifesto Database
#' 
#' Internal implementation. For more convenient access and caching use one of 
#' \code{\link{mp_corpus}}, 
#' \code{\link{mp_availability}},  
#' \code{\link{mp_maindataset}}.
#'
#' @param type string of \code{"meta", "text", "original", "main", "versions"} 
#'             to indicate type of content to get
#' @param parameters content filter parameters specific to type
#' @param versionid character string specifying the corpus version to use, either
#'        a name or tag as in the respective columns of the value of
#'        \code{\link{mp_corpusversions}} and the API
#' @param apikey API key to use, defaults to \code{NULL}, which means the key 
#'               currently stored in the variable \code{apikey} of the
#'               environment \code{mp_globalenv} is used.
get_mpdb <- function(type, parameters=c(), versionid=NULL, apikey=NULL) {

  # check api key
  if (is.null(apikey)) {
    apikey <- get(kapikey, envir = mp_globalenv)
  }
  if (is.na(apikey) && !type %in% c(kmtype.versions, kmtype.codebook)) {
    stop(kmerror.keymissing)
  }


  # select URL
  if (type == kmtype.versions) {
    requestfile <- "list_core_versions"
  } else if (type == kmtype.main) {
    requestfile <- "get_core"
  } else if (type == kmtype.meta) {
    requestfile <- "metadata"
  } else if (type == kmtype.text) {
    requestfile <- "texts_and_annotations"
  } else if (type == kmtype.metaversions) {
    requestfile <- "list_metadata_versions"
    parameters <- c(parameters, tag = "true")
  } else if (type == kmtype.corecitation) {
    requestfile <- "get_core_citation"
  } else if (type == kmtype.corpuscitation) {
    requestfile <- "get_corpus_citation"
  } else if (type == kmtype.codebook) {
    requestfile <- "get_core_codebook"
  } else if (type == kmtype.parties) {
    requestfile <- "get_parties"
  }

  # prepare version parameter if needed
  if (type %in% c(kmtype.meta, kmtype.text)) {
    if (is.null(versionid)) {
      versionid <- last_corpus_version(apikey = apikey)
    }
    parameters <- c(parameters, version = versionid)
  }

  # get content from web
  jsonstr <- mpdb_api_request(file=requestfile,
                              body=toamplist(parameters),
                              apikey=apikey)

  # convert to desired format (before caching)
  if (type %in% c(kmtype.versions, kmtype.corecitation, kmtype.corpuscitation)) {

    return(data.frame(fromJSON(jsonstr), stringsAsFactors = FALSE))

  } else if (type == kmtype.metaversions) {

    return(fromJSON(jsonstr)$versions)    

  } else if (type == kmtype.main) {
    
    if (is.null(parameters$kind)) {
      return(formatmpds(data.frame(fromJSON(jsonstr), stringsAsFactors = FALSE)))
    } else {
      return(jsonstr %>%
               fromJSON() %>%
               getElement("content"))
    }

  } else if (type == kmtype.meta) {

    metadata <- data.frame(separate_missings(fromJSON(jsonstr), request="metadata"), stringsAsFactors = FALSE) %>%
      mutate_all(as.character)

    if (nrow(metadata) > 0) {
      names(metadata)[which(names(metadata)=="party_id")] <- "party"
      names(metadata)[which(names(metadata)=="election_date")] <- "date"
      
      ## convert types
      metadata <- within(metadata, {
        party <- as.numeric(party)
        date <- as.numeric(date)
        if (exists("annotations")) annotations <- as.logical(annotations)
        if (exists("is_primary_doc")) is_primary_doc <- as.logical(is_primary_doc)
        if (exists("may_contradict_core_dataset")) may_contradict_core_dataset <- as.logical(may_contradict_core_dataset)
        if (exists("has_eu_code")) has_eu_code <- as.logical(has_eu_code)
      })      
    }

    return(metadata)
  
  } else if (type == kmtype.text) {

    texts <- separate_missings(fromJSON(jsonstr), request="text")
    names(texts)[which(names(texts)=="key")] <- "manifesto_id"
    
    return(texts)

  } else if (type == kmtype.codebook) {
    
    jsonstr %>%
      fromJSON() %>%
      as_tibble(.name_repair = "minimal") %>%
      { set_names(., as.character(.[1,])) } %>%
      dplyr::slice(2:n()) %>%
      magrittr::set_rownames(NULL)
        
  } else if (type == kmtype.parties) {

    jsonstr %>%
      fromJSON() %>%
      as_tibble(.name_repair = "minimal") %>%
      { set_names(., as.character(.[1,])) } %>%
      dplyr::slice(2:n()) %>%
      magrittr::set_rownames(NULL) %>%
      formatpartiesds()

  }
}

get_citation <- function(version, type, apikey = NULL) {
  get_mpdb(type,
           parameters = list(key = version),
           apikey = apikey)$citation %>% unlist()
}

last_corpus_version <- function(onlytag = TRUE, apikey = NULL, ...) {
  mp_corpusversions(apikey = apikey) %>%
    subset(!onlytag | !is.na(tag)) %>%
    arrange(name) %>%
    tail(n=1) %>%
    with(ifelse(is.na(tag), name, tag))
}
