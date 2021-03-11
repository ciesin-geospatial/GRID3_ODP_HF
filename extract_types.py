import re
import unidecode
from collections import Counter


def deaccent(input_string):
    output_string = unidecode.unidecode(input_string)
    return output_string


def remove_special_characters_and_shrink_whitespace(input_string):
    output_string = re.sub(r'\s+', ' ', re.sub(r'[^A-Za-z0-9\s]', '', input_string))
    return output_string


def clean_string(input_string):
    output_string = remove_special_characters_and_shrink_whitespace(deaccent(input_string.lower()))
    return output_string


def get_unique_ngram(list_of_ordered_tokens, n):
    # Get the unique ngrams in a string, given a list of ordered tokens in that string
    return set(zip(*[list_of_ordered_tokens[i:i - (n - 1)] if i < n - 1 else list_of_ordered_tokens[n - 1:] for i in range(0, n)]))


def reduce_nested_ngram_freq(x, ngram_freq, mutable_ngram_freq):
    max_matched_n = 0  # Length of the longest ngram(s) we have matched for this name
    # Note that we have ordered the ngram_freq such that longer ngrams come first, so we can expect to match longest ngram asap

    for n, ngram, count in ngram_freq:
        # If the current ngram occurred in more than one name AND the ngram is in the current name
        if count > 1 and ' ' + ngram + ' ' in ' ' + x + ' ':
            # If the current ngram is at least the same or even longer than the max n we matched,
            # just update the max n and move on
            if n >= max_matched_n:
                max_matched_n = n
            else:
                # Else if the current ngram is shorter than longest ngram we have matched in this name,
                # this probably suggests the current ngram is part of the longest ngram we matched before,
                # thus we need to decrease the frequency count for this shorter ngram as it is not an independent count
                mutable_ngram_freq[ngram] -= 1


def strip_preposition(input_string, prepositions='al,el,at,et,la,le,les,da,de,do,du,des,das,and,of,for'):
    output_string = input_string.strip()
    for preposition in prepositions.split(',') if isinstance(prepositions, str) else prepositions:
        output_string = re.sub(r'^' + preposition + '$', '', output_string)
        output_string = re.sub(r'^' + preposition + ' ', '', output_string)
        output_string = re.sub(r' ' + preposition + '$', '', output_string)
    return output_string


def strip_number_prefix(input_string, numbers='i,ii,iii,iv,v,vi,vii,viii,ix,x'):
    output_string = input_string.strip()
    for number in numbers.split(',') if isinstance(numbers, str) else numbers:
        output_string = re.sub(r'^' + number + '$', '', output_string)
        output_string = re.sub(r'^' + number + ' ', '', output_string)
    output_string = re.sub(r'^\d+$', '', output_string)
    output_string = re.sub(r'^\d+ ', '', output_string)
    return output_string


def consolidate_count_list(input_list):
    output_list = [(item, count) for item, count in input_list if item.strip() != '' and len(item) > 1]
    dic = {}
    for item, count in output_list:
        if dic.get(item) is None:
            dic[item] = count
        else:
            dic[item] += count
    output_list = sorted(list(dic.items()), key=lambda x: -x[-1])
    return output_list


def health_facility_rules(input_list):
    output_list = [(strip_preposition(strip_number_prefix(item)), count) for item, count in input_list]
    output_list = consolidate_count_list(output_list)
    return output_list

def extract_types(input_list, thres=None, maximum_expected_number_of_types=20, return_proportion=False, custom_rule=health_facility_rules):
    '''
    Given a list of names, return the common types in the names along with their frequency
    '''
    name_list = [clean_string(name) for name in list(input_list)]
    number_of_names_in_this_list = len(name_list)

    phrase_counter = Counter()
    # For each name in the name list, tokenize it and count the ngrams in the name,
    # and add the frequency of ngrams to the phrase counter
    for name in name_list:
        tokens_in_name = name.strip().split(" ")
        for n in range(1, min(len(tokens_in_name), 10) + 1):  # Record frequency of ngrams up to 10 tokens' long
            phrase_counter.update(get_unique_ngram(tokens_in_name, n))

    # For each pair of (token_sequence, count) in the phrase_counter, convert it to (n, ngram, count), where n is the "n" in ngram
    ngram_freq = [(len(token_sequence), ' '.join(token_sequence), count) for token_sequence, count in phrase_counter.most_common() if count >= round(len(name_list) * 0.001)]

    # Sort the ngram_freq list in the reverse order of n, such that longer ngrams is earlier in the list
    ngram_freq = sorted(ngram_freq, key=lambda entry: -entry[0])

    # Create a mutable copy of the ngram_freq list
    mutable_ngram_freq = {ngram: count for n, ngram, count in ngram_freq}

    # Iterate through all the names in the name list, use the reduce the frequency count for the ngrams that are part of longer ngram
    for name in name_list:
        reduce_nested_ngram_freq(name, ngram_freq, mutable_ngram_freq)

    sorted_consolidated_ngram_freq = sorted(list(mutable_ngram_freq.items()), key=lambda t: -t[-1])

    # If thres is not provided, return the top k types found, with k defined by maximum_expected_number_of_types
    if thres is None:
        if len(sorted_consolidated_ngram_freq) > maximum_expected_number_of_types:
            minimum_count = sorted_consolidated_ngram_freq[maximum_expected_number_of_types][-1]
        else:
            minimum_count = 1
    # If thres is provided, calculate the minimum count by multiplying threshold with number of names in the list
    else:
        minimum_count = int(thres * number_of_names_in_this_list)

    minimum_count = max(1, minimum_count)

    sorted_consolidated_ngram_freq = [item for item in sorted_consolidated_ngram_freq if item[-1] > minimum_count]

    no_full_coverage_list = [(item, count) for item, count in sorted_consolidated_ngram_freq if item not in name_list]

    if custom_rule:
        results = custom_rule(no_full_coverage_list)
    else:
        results = no_full_coverage_list

    # If return_proportion is true, return the results in the format (ngram, proportion, count)
    if return_proportion:
        results = [(item, round(count / number_of_names_in_this_list, 3), count) for item, count in results]

    return results
