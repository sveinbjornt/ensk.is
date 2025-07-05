import math
import morfessor


# function for adjusting the counts of each compound
def log_func(x):
    return int(round(math.log(x + 1, 2)))


infile = "data/wordlists/nltk_words.txt"
io = morfessor.MorfessorIO()
train_data = list(io.read_corpus_file(infile))
model = morfessor.BaselineModel()
model.load_data(train_data, count_modifier=log_func)
model.train_batch()
io.write_binary_model_file("model.bin", model)
