from django.http import JsonResponse
from .scripts.data_process import process_data
from django.shortcuts import render
import pandas as pd
import numpy as np
import os
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
import seaborn as sns
import matplotlib.pyplot as plt


@login_required
def upload_file(request):
    print("upload_file() function called")
    if request.method == 'POST':
        uploaded_file = request.FILES['fileup']
        file_path = os.path.join(settings.MEDIA_ROOT, 'uploaded.csv')
        with open(file_path, 'wb+') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        return redirect('process')
    else:
        return render(request, 'upload.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('your_name')
        password = request.POST.get('your_pass')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('fileup')
    context = {}
    return render(request, 'login.html', context)


def logout_view(request):
    logout(request)
    return redirect('login')


def about(request):
    return render(request, 'about.html')


@login_required
def process(request):
    return render(request, 'process.html')


@login_required
def process_data_ajax(request):
    file_path = os.path.join(settings.MEDIA_ROOT, 'uploaded.csv')

    print("process code called")

    # Call the process_data function
    common_skills, missing_skills = process_data(file_path)

    # Export the dataframes to csv files
    common_skills.to_csv(os.path.join(
        settings.MEDIA_ROOT, 'common.csv'), index=False)
    missing_skills.to_csv(os.path.join(
        settings.MEDIA_ROOT, 'missing.csv'), index=False)

    # PLOTS #

    labels = ['Web Development', 'Big Data',
              'Machine Learning', 'Deep Learning', 'Security']

    # MISSING PLOT

    # Set the figure size and create two subplots side by side
    fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(12, 5))

    # Count the number of missing skills per category
    missing_counts = missing_skills.astype(bool).sum(axis=0)

    # Create a pie chart of the missing skill counts using Seaborn
    sns.set_palette("Set2")
    sns.set(font_scale=1.0)
    sns.set_style("whitegrid")
    ax1.pie(missing_counts.values, labels=labels,
            autopct='%1.1f%%', startangle=90)

    # Set the chart title
    ax1.set_title('Missing Skills in Curriculum')

    # Count the number of missing skills per category
    missing_counts = missing_skills.astype(bool).sum(axis=0)

    # Create a bar chart of the missing skill counts using Seaborn
    sns.barplot(x=labels, y=missing_counts.values, ax=ax2)

    # Set the chart title and axis labels
    ax2.set_title('Missing Skills in curriculum')
    ax2.set_ylabel('Number of Missing Skills')

    # Rotate the category labels for better readability
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)

    fig.suptitle('Missing Skills Analysis', fontsize=16)

    # Adjust the spacing between the subplots
    plt.subplots_adjust(wspace=1.0)

    # Save the plot to a temporary file
    plt.savefig('myapp/static/missing_plot.png', bbox_inches='tight')
    plt.close()

    # COMMON PLOT

    # Set the figure size and create two subplots side by side
    fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(12, 5))

    # Count the number of Common Skills per category
    common_counts = common_skills.astype(bool).sum(axis=0)

    # Create a pie chart of the missing skill counts using Seaborn
    sns.set_palette("Set2")
    sns.set(font_scale=1.0)
    sns.set_style("whitegrid")
    ax1.pie(common_counts.values, labels=labels,
            autopct='%1.1f%%', startangle=90)

    # Set the chart title
    ax1.set_title('Common Skills')

    # Count the number of Common Skills per category
    common_counts = common_skills.astype(bool).sum(axis=0)

    # Create a bar chart of the missing skill counts using Seaborn
    sns.barplot(x=labels, y=common_counts.values, ax=ax2)

    # Set the chart title and axis labels
    ax2.set_title('Common Skills')
    ax2.set_ylabel('Number of Common Skills')

    # Rotate the category labels for better readability
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)

    fig.suptitle('Common Skills Analysis', fontsize=16)

    # Adjust the spacing between the subplots
    plt.subplots_adjust(wspace=1.0)

    # Save the plot to a temporary file
    plt.savefig('myapp/static/common_plot.png', bbox_inches='tight')
    plt.close()

    # Return the result as a JSON response
    response = {
        'common_skills': 'common.csv',
        'missing_skills': 'missing.csv'
    }

    return JsonResponse(response)


@login_required
def dashboard(request):
    common_file_path = os.path.join(settings.MEDIA_ROOT, 'common.csv')
    missing_file_path = os.path.join(settings.MEDIA_ROOT, 'missing.csv')
    print(common_file_path)  # Print the common file path for debugging
    print(missing_file_path)  # Print the missing file path for debugging

    if (os.path.exists(common_file_path) and os.path.exists(missing_file_path)):
        # Read the common and missing files
        common_skills = pd.read_csv(common_file_path)
        missing_skills = pd.read_csv(missing_file_path)

        #___#
        common_skills = pd.DataFrame({
            col: sorted(common_skills[col], key=lambda x: (
                pd.isna(x), x))
            for col in common_skills.columns
        })
        common_skills.replace('', np.nan, inplace=True)

        common_skills.dropna(how='all', inplace=True)

        common_skills = common_skills.fillna('')
        #___#

        #___#
        missing_skills = pd.DataFrame({
            col: sorted(missing_skills[col], key=lambda x: (
                pd.isna(x), x))
            for col in missing_skills.columns
        })
        missing_skills.replace('', np.nan, inplace=True)

        missing_skills.dropna(how='all', inplace=True)

        missing_skills = missing_skills.fillna('')
        #___#

        # Pass the data to the template for rendering
        context = {
            'common': common_skills,
            'missing': missing_skills
        }
        print(context)
        return render(request, 'dashboard.html', context)
    else:
        print("not found")
        # No files found
        return render(request, 'dashboard.html', {})
