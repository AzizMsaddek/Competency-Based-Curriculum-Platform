import os
import argostranslate.package
import argostranslate.translate
from django.conf import settings
import pandas as pd
import numpy as np
import re
import string
import html
import nltk
from nltk.tokenize import word_tokenize


def process_data(file_path):

    data = pd.read_csv(file_path)

    data = data.astype(str)

    # Remove duplicate profiles
    data = data.drop_duplicates(subset=['Name'])

    # Remove text leading and trailing whitespaces
    data['Experiences'] = data['Experiences'].str.strip()
    data['Education'] = data['Education'].str.strip()

    # Remove empty experiences
    data = data[~data['Experiences'].isin(['', 'nan', 'No Result'])]

    # # Translation of Experiences to English
    # from_code = "fr"
    # to_code = "en"

    # # Download and install Argos Translate package
    # argostranslate.package.update_package_index()
    # available_packages = argostranslate.package.get_available_packages()
    # package_to_install = next(
    #     filter(
    #         lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
    #     )
    # )
    # argostranslate.package.install_from_path(
    #     package_to_install.download())  # type: ignore

    # # Define a function to translate a text from French to English
    # def translate_fr_to_en(text):
    #     if isinstance(text, str):
    #         translatedText = argostranslate.translate.translate(
    #             text, from_code, to_code)
    #         return translatedText
    #     else:
    #         return text

    # # Apply the translation function to the Experiences column
    # data['Experiences'] = data['Experiences'].apply(translate_fr_to_en)

    # Download he necessary NLTK resources
    nltk.download(['punkt', 'stopwords', 'wordnet'])
    from nltk.corpus import stopwords

    def clean_string(text):
        # Replace HTML entity codes
        text = html.unescape(text)

        final_string = ""

        # Make lower
        text = text.lower()

        # Remove line breaks
        text = re.sub(r'\n', '', text)

        # # Remove puncuation
        translator = str.maketrans(
            string.punctuation, ' ' * len(string.punctuation))
        text = text.translate(translator)

        # Tokenize text
        tokens = word_tokenize(text)

        # Remove stop words
        useless_words = stopwords.words("english")
        text_filtered = [
            token for token in tokens if not token in useless_words]

        # Remove non-alphabetic characters
        text_filtered = [re.sub(r'[^a-zA-Z.,\-]', '', w)
                         for w in text_filtered]

        # Re-join text
        final_string = ' '.join(text_filtered)

        return final_string

    DS_data = pd.DataFrame(data['Experiences'].apply(
        lambda x: clean_string(x)).tolist(), columns=['Experiences'])

    from keybert import KeyBERT

    kw_model = KeyBERT()

    # Define a function to extract keywords for each row
    def extract_keywords(doc):
        """
        This function extracts the top 10 keywords from a given document using KeyBERT
        """
        keyphrases = kw_model.extract_keywords(
            doc, keyphrase_ngram_range=(1, 2), top_n=10)
        keywords = list(set([keyword for keyword, score in keyphrases]))
        return keywords

    def process_skills(df):
        skills = pd.DataFrame(df['Experiences'].apply(extract_keywords).tolist(),
                              columns=['skill_1', 'skill_2', 'skill_3', 'skill_4', 'skill_5', 'skill_6',
                                       'skill_7', 'skill_8', 'skill_9', 'skill_10'])
        return skills

    DS_skills = process_skills(DS_data)

    df = pd.read_csv(os.path.join(settings.MEDIA_ROOT, 'technologies.csv'))

    DS_curriculum = pd.read_excel(os.path.join(
        settings.MEDIA_ROOT, 'Fiche-DS.xlsx'))

    # Convert the csv file into a dataframe
    techs_df = pd.DataFrame(df).fillna('')

    # Import the fuzzywuzzy library
    from fuzzywuzzy import fuzz

    # Define a function to match skills using fuzzy matching and exact matching
    def match_skill(skill, skill_list):
        '''
        Matches a skill in skill_list using Fuzzy Matching
        '''
        # Loop through each skill in the IT Skills dataset
        for tech in skill_list:
            # Calculate the similarity score between the two skills using fuzzy matching
            score = fuzz.ratio(skill.lower(), tech.lower())
            # If the similarity score is above a certain threshold, return the matching skill
            if score >= 60:
                return tech

    def filter_skills(skills, techs_df):

        def match_category(skill):
            '''
                Returns all categories that match 'skill'
            '''
            matches = []

            for category in techs_df.columns:
                exact_match = techs_df[category].str.lower(
                ).str.contains(skill.lower()).any()
                if exact_match:
                    matches.append(category)
                else:
                    for tech in techs_df:
                        score = fuzz.ratio(skill.lower(), tech.lower())
                        if score >= 50:
                            matches.append(category)
            return matches

        # Create an empty dictionary to store the matched skills
        matched_skills = {category: [] for category in techs_df.columns}

        # Apply the match_category function to each skill in the skills dataset
        for col in skills.columns:
            for skill in skills[col].dropna().unique():
                categories = match_category(skill)
                if categories:
                    for category in categories:
                        matched_skill = match_skill(
                            skill, techs_df[category].dropna().unique())
                        if matched_skill:
                            matched_skills[category].append(matched_skill)

        # Define a function to remove duplicates in a list and return the result
        def remove_duplicates(x):
            if isinstance(x, list):
                return list(set(x))
            else:
                return x

        # Apply the remove_duplicates function to each column in the matched_skills dictionary
        for category in matched_skills:
            matched_skills[category] = remove_duplicates(
                matched_skills[category])

        # Append None to shorter lists to ensure they are of the same length
        max_length = max([len(x) for x in matched_skills.values()])
        for category in matched_skills:
            matched_skills[category] += [None] * \
                (max_length - len(matched_skills[category]))

        # Convert the matched_skills dictionary to a sorted pandas dataframe
        matched_skills_df = pd.DataFrame.from_dict(matched_skills).apply(
            lambda x: x.sort_values().reset_index(drop=True), axis=0).fillna('')

        return matched_skills_df

    DS_filtered_skills = filter_skills(DS_skills, techs_df)

    # MISSING SKILLS

    # Find the skills in DS_filtered_skills that don't exist in DS_curriculum
    missing_skills = DS_filtered_skills[~DS_filtered_skills.isin(
        DS_curriculum)].dropna(how='all')

    # Use fuzzy matching to find similar skills between the two dataframes
    for col in missing_skills.columns:
        for i, skill in missing_skills[col].dropna().items():
            for j, curriculum_skill in DS_curriculum[col].dropna().items():
                # Compare the two skills using fuzzy matching
                ratio = fuzz.ratio(skill.lower(), curriculum_skill.lower())
                if ratio >= 70:
                    # If the ratio is high enough, assume the two skills are the same
                    missing_skills.loc[i, col] = ''
                    break

    # Rearrange the missing skills dataframe to match the original structure
    missing_skills = missing_skills.reindex(columns=DS_filtered_skills.columns)

    missing_skills.columns = ['Web_Development', 'Big_Data',
                              'Machine_Learning', 'Deep_Learning', 'Security']

    # Replace any NaN values with an empty string
    missing_skills = missing_skills.fillna('')

    # COMMON SKILLS

    # Use fuzzy matching to find similar skills between the two dataframes
    common_skills = pd.DataFrame(columns=DS_filtered_skills.columns)
    for col in DS_filtered_skills.columns:
        for i, skill in DS_filtered_skills[col].dropna().items():
            for j, curriculum_skill in DS_curriculum[col].dropna().items():
                # Compare the two skills using fuzzy matching
                ratio = fuzz.ratio(skill.lower(), curriculum_skill.lower())
                if ratio >= 70:
                    # If the ratio is high enough, assume the two skills are the same
                    common_skills.loc[i, col] = skill
                    break

    common_skills.columns = common_skills.columns.str.replace(' ', '_')

    common_skills = common_skills.fillna('')

    return common_skills, missing_skills
