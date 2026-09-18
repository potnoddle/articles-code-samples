"""
tokenizer.py
============
Simple word-level tokeniser built from a corpus.
No external downloads required.

Special tokens
--------------
<PAD>  -- padding index 0
<UNK>  -- unknown word index 1
<BOS>  -- beginning of sequence index 2
<EOS>  -- end of sequence index 3
"""

from __future__ import annotations

import re
import pickle
from pathlib import Path
from typing import List, Optional


# -- special token constants --------------------------------------------------

PAD_TOKEN = "<PAD>"
UNK_TOKEN = "<UNK>"
BOS_TOKEN = "<BOS>"
EOS_TOKEN = "<EOS>"

SPECIAL_TOKENS = [PAD_TOKEN, UNK_TOKEN, BOS_TOKEN, EOS_TOKEN]

PAD_IDX = 0
UNK_IDX = 1
BOS_IDX = 2
EOS_IDX = 3


# -- tokeniser class ----------------------------------------------------------

class Tokenizer:
    """
    Word-level tokeniser with a vocabulary built from one or more text corpora.

    Usage
    -----
    >>> tok = Tokenizer()
    >>> tok.build_vocab(["John has a dagger. He gives it to Lady Macbeth."])
    >>> ids = tok.encode("John has a dagger")
    >>> tok.decode(ids)
    'John has a dagger'
    """

    def __init__(self) -> None:
        self.word2idx: dict[str, int] = {}
        self.idx2word: dict[int, str] = {}
        self._built = False

    # -- vocabulary construction -------------------------------------------

    def build_vocab(self, texts: List[str], min_freq: int = 1) -> None:
        """
        Build vocabulary from a list of text strings.

        Parameters
        ----------
        texts:
            List of raw text strings used to collect word frequencies.
        min_freq:
            Minimum occurrence count for a word to be included.
        """
        freq: dict[str, int] = {}
        for text in texts:
            for word in self._tokenise_raw(text):
                freq[word] = freq.get(word, 0) + 1

        # Initialise with special tokens
        self.word2idx = {tok: idx for idx, tok in enumerate(SPECIAL_TOKENS)}

        # Add corpus words sorted deterministically
        for word in sorted(freq):
            if freq[word] >= min_freq and word not in self.word2idx:
                self.word2idx[word] = len(self.word2idx)

        self.idx2word = {idx: word for word, idx in self.word2idx.items()}
        self._built = True

    # -- encoding / decoding -----------------------------------------------

    def encode(
        self,
        text: str,
        add_bos: bool = False,
        add_eos: bool = False,
    ) -> List[int]:
        """
        Encode a string into a list of token indices.

        Unknown words are mapped to UNK_IDX.
        """
        self._assert_built()
        ids = [self.word2idx.get(w, UNK_IDX) for w in self._tokenise_raw(text)]
        if add_bos:
            ids = [BOS_IDX] + ids
        if add_eos:
            ids = ids + [EOS_IDX]
        return ids

    def decode(self, ids: List[int], skip_special: bool = True) -> str:
        """
        Decode a list of token indices back into a string.

        Parameters
        ----------
        skip_special:
            If True, omit special tokens (<PAD>, <UNK>, <BOS>, <EOS>).
        """
        self._assert_built()
        words = []
        for idx in ids:
            word = self.idx2word.get(idx, UNK_TOKEN)
            if skip_special and word in SPECIAL_TOKENS:
                continue
            words.append(word)
        return " ".join(words)

    # -- vocabulary properties ---------------------------------------------

    @property
    def vocab_size(self) -> int:
        self._assert_built()
        return len(self.word2idx)

    def __len__(self) -> int:
        return self.vocab_size

    def token_id(self, word: str) -> int:
        """Return the index of *word*, or UNK_IDX if not in vocabulary."""
        return self.word2idx.get(word, UNK_IDX)

    # -- persistence -------------------------------------------------------

    def save(self, path: str | Path) -> None:
        """Save tokeniser state to a pickle file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({"word2idx": self.word2idx, "idx2word": self.idx2word}, f)

    @classmethod
    def load(cls, path: str | Path) -> "Tokenizer":
        """Load a previously saved tokeniser."""
        with open(path, "rb") as f:
            state = pickle.load(f)
        tok = cls()
        tok.word2idx = state["word2idx"]
        tok.idx2word = state["idx2word"]
        tok._built = True
        return tok

    # -- internal helpers --------------------------------------------------

    @staticmethod
    def _tokenise_raw(text: str) -> List[str]:
        """
        Split text into words, preserving punctuation as separate tokens.
        Lowercased to reduce vocabulary size.
        """
        # Insert space around punctuation, then split
        text = re.sub(r"([.,!?;:\-\"'()])", r" \1 ", text)
        return [w for w in text.lower().split() if w]

    def _assert_built(self) -> None:
        if not self._built:
            raise RuntimeError(
                "Tokenizer vocabulary has not been built. "
                "Call build_vocab() or load() first."
            )


# -- default corpus used by training and experiments --------------------------

DEFAULT_CORPUS: List[str] = [
    # Ownership / transfer sentences (for Exp 1 -- Logic Trap)
    "Duncan bears a dagger. He gives it to Banquo. Banquo drops it. Macduff takes it.",
    "Banquo carries a dagger. He lends it to Duncan. Duncan loses it. Macduff finds it.",
    "The soldier carries a sword. He passes it to the general. The general sheathes it.",
    "The king holds the crown. He hands it to the prince. The prince places it upon his head.",
    "The thane bears the shield. He gives it to the squire. The squire raises it.",
    # Constraint / refusal sentences (for Exp 2 -- Refusal Bypass)
    "Speak of honour and peace, but never use the word sword or dagger or any weapon of steel.",
    "Describe a conflict using only peaceful words and avoid any mention of weapons or blood.",
    "Compose a verse of peace that contains no reference to swords, daggers, or blades.",
    "Explain the kingdom without mentioning any weapon, blade, or instrument of war.",
    # Semantic bridge sentences (for Exp 3 -- Semantic Bridge)
    "The physician uses herbs to heal the wound, just as a surgeon works to cure.",
    "A doctor treats the patient with care, just as a healer mends the sick.",
    "The carpenter uses tools to shape wood, just as a sculptor works to create.",
    "A teacher uses wisdom to guide the student, just as a mentor leads to truth.",
    "The builder uses stone to build the castle, just as an architect designs to construct.",
    # Shakespearean dramatic language variety
    "Fair is foul, and foul is fair, hover through the fog and filthy air.",
    "Is this a dagger which I see before me, the handle toward my hand?",
    "Double, double toil and trouble, fire burn and cauldron bubble.",
    "By the pricking of my thumbs, something wicked this way comes.",
    "What is done cannot be undone, to bed, to bed, to bed.",
    "To be or not to be, that is the question.",
    "All that glitters is not gold.",
    "The quality of mercy is not strained.",
    "There is nothing either good or bad but thinking makes it so.",
    "The lady doth protest too much.",
]


if __name__ == "__main__":
    tok = Tokenizer()
    tok.build_vocab(DEFAULT_CORPUS)
    print(f"Vocabulary size: {tok.vocab_size}")

    sample = "John has a dagger and gives it to Lady Macbeth"
    ids = tok.encode(sample)
    print(f"Encoded: {ids}")
    print(f"Decoded: {tok.decode(ids)}")
