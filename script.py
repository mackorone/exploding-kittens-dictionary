#!/usr/bin/env python3

import argparse
import asyncio
import logging
from typing import Dict, Set

import aiohttp

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger: logging.Logger = logging.getLogger(__name__)


LISTS_OF_ENGLISH_WORDS = [
    "https://raw.githubusercontent.com/jeremy-rifkin/Wordlist/master/master.txt",
    "https://raw.githubusercontent.com/mwdean/english-wordz/master/words_alpha.txt",
    # The following lists don't contribute any additional words beyond the lists above:
    # - https://raw.githubusercontent.com/dolph/dictionary/master/unix-words
    # - https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt
    # - https://raw.githubusercontent.com/jmlewis/valett/master/scrabble/sowpods.txt
    # - https://raw.githubusercontent.com/sindresorhus/word-list/main/words.txt
    # - https://raw.githubusercontent.com/zeisler/scrabble/master/db/dictionary.csv
    # - https://scrabutility.com/TWL06.txt
]


async def generate_word_list(output: str, chunk_size: int) -> None:
    async with aiohttp.ClientSession() as session:
        # Fetch the lists of words
        coros = [fetch_words(session, url) for url in LISTS_OF_ENGLISH_WORDS]
        results = await asyncio.gather(*coros)
        url_to_words: Dict[str, Set[str]] = dict(zip(LISTS_OF_ENGLISH_WORDS, results))
        all_words = {word for set_ in url_to_words.values() for word in set_}
        sorted_words = sorted(all_words)

        # Get the smallest multiple of chunk_size less than len(sorted_words)
        numerator_width = len(
            str(len(sorted_words) - ((len(sorted_words) - 1) % chunk_size))
        )

        # Filter invalid words
        logger.info(f"Checking the validity of all {len(sorted_words)} words...")
        valid_words: Set[str] = set()
        with open(output, "w") as f:
            for i in range(0, len(sorted_words), chunk_size):
                numerator = str(i).rjust(numerator_width)
                progress_fraction = i / len(sorted_words)
                progress_percent = f"{progress_fraction:.0%}".rjust(3)
                logger.info(f"{numerator} / {len(sorted_words)} ({progress_percent})")
                candidates = sorted_words[i : i + chunk_size]  # noqa: E203
                coros = [is_valid_word(session, word) for word in candidates]
                results = await asyncio.gather(*coros)
                for word, is_valid in zip(candidates, results):
                    if is_valid:
                        valid_words.add(word)
                        print(word, file=f)

    # Determine which lists contribute the most valid words
    logger.info("Printing contribution amounts...")
    url_to_count = compute_contributions(url_to_words, valid_words)
    max_count = max(url_to_count.values())
    for url, count in sorted(
        url_to_count.items(), key=lambda pair: (-pair[1], pair[0])
    ):
        logger.info(f"{str(count).rjust(len(str(max_count)))}: {url}")


async def fetch_words(session: aiohttp.ClientSession, url: str) -> Set[str]:
    logger.info(f"Fetching word list: {url}")
    async with session.get(url) as response:
        text = await response.text()
    words: Set[str] = set()
    for word in text.splitlines():
        word = word.strip().lower()
        if word:
            words.add(word)
    return words


async def is_valid_word(session: aiohttp.ClientSession, word: str) -> bool:
    # From https://ek.explodingkittens.com/js/dictionary.js?q=2021062301
    url = f"https://d3hgrnpazz7n9u.cloudfront.net/allowedWords?word={word}"
    num_attempts = 3
    for i in range(num_attempts):
        try:
            async with session.get(url) as response:
                result = await response.json()
            assert result["word"].lower() == word
            return result["allowed"]
        except Exception:
            if i == num_attempts - 1:
                raise
            logger.exception(f"Failed to validate word: {word}")
            await asyncio.sleep(1)
    assert False  # for pyre


def compute_contributions(
    url_to_words: Dict[str, Set[str]], words: Set[str]
) -> Dict[str, int]:
    url_to_count: Dict[str, int] = {}
    remaining_urls = set(url_to_words)
    remaining_words = set(words)
    while remaining_urls and remaining_words:
        url_to_remaining_words = {
            url: (url_to_words[url] & remaining_words) for url in remaining_urls
        }
        url, words = max(
            url_to_remaining_words.items(), key=lambda pair: (len(pair[1]), pair[0])
        )
        url_to_count[url] = len(words)
        remaining_urls.remove(url)
        remaining_words -= words
    return url_to_count


def main():
    parser = argparse.ArgumentParser(description="Generate a list of valid words")
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="The path to the output file",
    )
    parser.add_argument(
        "--chunk",
        type=int,
        default=100,
        help="The number of words to validate concurrently",
    )
    args = parser.parse_args()
    asyncio.run(generate_word_list(output=str(args.output), chunk_size=int(args.chunk)))


if __name__ == "__main__":
    main()
