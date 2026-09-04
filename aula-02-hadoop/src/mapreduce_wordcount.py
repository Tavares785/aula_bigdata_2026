from mrjob.job import MRJob
import re


STOPWORDS = {
    "a", "o", "os", "as", "de", "da", "do", "das", "dos", "e", "que",
    "em", "um", "uma", "para", "com", "no", "na", "nos", "nas", "se",
    "por", "sua", "seu", "ao", "à", "às",
}


WORD_RE = re.compile(r"[A-Za-zÀ-ÿ]+")


class MRWordFrequencyCount(MRJob):

    def mapper(self, _, line):
        for word in WORD_RE.findall(line.lower()):
            if word not in STOPWORDS:
                yield word, 1

    def combiner(self, word, counts):
        yield word, sum(counts)

    def reducer(self, word, counts):
        yield word, sum(counts)


if __name__ == "__main__":
    MRWordFrequencyCount.run()