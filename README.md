# w210-capstone
Determining Species Count in Protected Areas Through Image Recognition.

## Overview

Poaching continues to pose a threat to the survival of endangered species, even on protected land. Tracking individual animals and maintaining species counts is essential in combating this threat, by allowing conservationists to determine the impact of natural changes vs poaching impact and deciding where and when to deploy resources to protect the animals. However, current methods of identifying and counting individual animals are time-consuming and limit the ability to protect them in a timely manner.

Our solution to this problem is to automate the process of identifying individual animals in camera-trap still images, allowing conservationists to more quickly check and correct individual animal labels if necessary. Using publicly available datasets for individual animal identification, we successfully implemented models to predict more than 800 unique animals across 3 species and developed an interactive tool to allow users to view predicted labels and make corrections as needed.

## Launching the Application

Here is the link to the front end UI: https://groups.ischool.berkeley.edu/safari_sleuths/

And the steps on how to execute the end-to-end modeling process:

1. Create a new collection or choose an existing collection
2. Upload photo(s)
3. Compute the prediction results
4. Accept, reject, or edit the annotations
5. Retrain the model to recompute the prediction results
