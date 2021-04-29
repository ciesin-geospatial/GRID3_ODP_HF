import re
from collections import Counter
import unicodedata
import math


def remove_accents(input_str):
    # https://stackoverflow.com/a/517974
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


def remove_special_characters_and_shrink_whitespace(input_string):
    output_string = re.sub(r'\s+', ' ', re.sub(r'[^A-Za-z0-9\s]', '', input_string))
    return output_string


def clean_string(input_string):
    if (isinstance(input_string, str) and input_string.strip() != '') or (not math.isnan(input_string)):
        return remove_special_characters_and_shrink_whitespace(remove_accents(str(input_string).lower()))
    else:
        return ''


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


def print_table(table_data):

    table_data = [list(tup) for tup in table_data]

    no_percentage = False
    float_rounding = 3

    format_string = ''

    for i in range(len(table_data[0])):
        this_column = [tup[i] for tup in table_data]

        if isinstance(this_column[0], str):
            column_type = 'str'
            max_string_len = max([len(x) for x in this_column])
            max_string_len = max(10, max_string_len + 5)
            format_string += '{: <' + str(max_string_len) + '}'

        elif isinstance(this_column[0], float):
            if no_percentage:
                column_type = 'float'
            else:
                if max(this_column) <= 1 and min(this_column) >= 0:
                    column_type = 'percentage'
                    d = 0  # find the number of digits till which there are value other than zero
                    while not all([x * (10**d) == int(x * (10**d)) for x in this_column]):
                        d += 1
                        if d > 6:
                            break
                    float_rounding = d - 2
                    format_string += '{: >10.' + str(float_rounding) + '%}'
                else:
                    column_type = 'float'
            if column_type == 'float':
                max_abs_num_len = len(str(int(max([abs(x) for x in this_column]))))
                max_abs_num_len = max(10, max_abs_num_len + 5 + float_rounding)
                format_string += '{: >' + str(max_abs_num_len) + '}'
            this_column = [round(x, float_rounding) for x in this_column]
        elif isinstance(this_column[0], int):
            column_type = 'int'
            max_abs_num_len = len(str(int(max([abs(x) for x in this_column]))))
            max_abs_num_len = max(10, max_abs_num_len + 5)
            format_string += '{: >' + str(max_abs_num_len) + '}'

    if column_type == 'percentage':
        for j in range(len(table_data)):
            table_data[j][i] *= 100

    for row in table_data:
        print(format_string.format(*row))


def extract_types(input_list, thres=None, maximum_expected_number_of_types=20, return_proportion=False, no_full_match=False, custom_rule=health_facility_rules):
    '''
    Given a list of names, return the common types in the names along with their frequency
    '''
    name_list = [str(x) for x in list(input_list) if (isinstance(x, str) and x.strip() != '') or (not math.isnan(x))]
    name_list = [clean_string(name) for name in name_list]
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
        if thres < 1 and thres >= 0:
            minimum_count = int(thres * number_of_names_in_this_list)
        elif thres >= 1 and int(thres) == thres:
            minimum_count = thres

    minimum_count = max(1, minimum_count)

    results = [item for item in sorted_consolidated_ngram_freq if item[-1] > minimum_count]

    if no_full_match:  # Should remove items whose occurrences are all full match in the list
        results = [(item, count) for item, count in results if item not in name_list]

    if custom_rule:
        results = custom_rule(results)

    # If return_proportion is true, return the results in the format (ngram, proportion, count)
    if return_proportion:
        results = [(item, round(count / number_of_names_in_this_list, 3), count) for item, count in results]

    print_table(results)

    return results


def match_type_string(entry, common_types):

    if isinstance(common_types[0], tuple):
        common_type_strings = [x[0] for x in sorted(common_types, key=lambda x: (-x[0].count(' '), -len(x[0])))]
    elif isinstance(common_types[0], str):
        pass
    else:
        raise

    for type_string in common_type_strings:
        if ' ' + type_string + ' ' in ' ' + entry + ' ':
            return type_string.strip()

    return math.nan
