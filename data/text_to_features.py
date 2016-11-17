from ngrams_corpus import GramCorpus
import sys
import os
import json
import logging
from six.moves import cPickle as pickle
import math


def create_bills_corpus(bills_dir, new_dir, row_to_bill):
    """Create a corpus of txt files from the bill informatation
    Input:
        bills_dir: string, path to directory with all the bills
        new_dir: string, path to directory to save corpus in
        row_to_bill: dict, mapping from row to bill info
    """
    # create a new directory for the corpus
    if not os.path.exists(new_dir):
        os.mkdir(new_dir)
        logging.info("Creating new directory " + new_dir)
    for row in row_to_bill.keys():
        bill_info = row_to_bill[row]
        category = bill_info["category"]
        if category == "bill":
            txt = bill_text(bills_dir, bill_info)
        elif category == "amendment":
            txt = amend_text(bill_info["file_name"])
        elif category == "nomination":
            txt = nom_text(bill_info["file_name"])
        # write the txt file
        row = row.zfill(math.ceil(math.log10(len(row_to_bill))))
        f_name = os.path.join(new_dir, "row_" + row + ".txt")
        with open(f_name, "w") as f:
            f.write(txt)


def bill_text(bills_dir, bill_info):
    """Get the summary text of a bill
    Input:
        bills_dir: string, path to directory with all the bills
        bill_info: dict, all the info we have about the bill
    Output:
        bill summary text
    """
    # get the type of bill and number
    b_type = bill_info["type"]
    b_num = bill_info["number"]
    # combine to get directory of the bill
    b_dir = os.path.join(os.path.join(bills_dir, b_type), b_type + str(b_num))
    # load the bill info as a json
    with open(os.path.join(b_dir, "data.json")) as f:
        bill_json = json.load(f)
    # return the text summary
    return(bill_json["summary"]["text"])


def amend_text(vote_file):
    """Get ammendment summary from the vote_file"""
    # load the json
    with open(vote_file) as f:
        vote_data = json.load(f)
    # get the purpose of the ammendment and use that as the text
    return(vote_data["amendment"]["purpose"])


def nom_text(vote_file):
    """Get nomination summary from the vote_file"""
    # load the json
    with open(vote_file) as f:
        vote_data = json.load(f)
    # get the title of the nomination (includes person and position)
    return(vote_data["nomination"]["title"])

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python text_to_features.py bills " +
              "combined_data/row_to_bill.json")
    else:
        bills_dir = sys.argv[1]
        with open(sys.argv[2]) as f:
            row_to_bill = json.load(f)
        # create a new directory for the corpus
        bills_dir = os.path.abspath(bills_dir)
        new_dir = os.path.join(os.path.split(bills_dir)[0], "bills_corpus")
        new_dir = os.path.relpath(new_dir)
        create_bills_corpus(bills_dir, new_dir, row_to_bill)

        # create a sparse bag of words feature matrix
        gc = GramCorpus(new_dir, 1, stop_words=False, punctuation=False)
        logging.info("Converting Corpus to sparse matrix")
        # get sparse matrix
        sparse = gc.to_sparse()
        # save sparse matrix and dictionary
        outdir = os.path.relpath("combined_data")
        with open(os.path.join(outdir, "bills_text.pkl"), "wb") as f:
            pickle.dump(sparse, f, protocol=2)
        with open(os.path.join(outdir, "bills_word_to_id.json"), "w") as f:
            # turn the gc.dictionary into a normal dict
            word_to_id = {w: i for w, i in gc.dictionary.items()}
            json.dump(word_to_id, f, sort_keys=True, indent=4)

