# Importing sys for easy script termination
import sys
# Importing JSON to handle request data
import json
# Importing requests library to perform network request
import requests
# Importing csv library to generate final csv file
import csv


def perform_nasa_api_query(searchTerm):
    """Receives a search term and queries the nasa image and video library API for results

    Arguments:
        searchTerm {string} -- The term to search for in the API

    Returns:
        Response object -- The response received from the NASA API
    """

    # Storing API search URL in variable
    url = "https://images-api.nasa.gov/search"
    # Storing our querystring in a variable
    querystring = {"q": searchTerm}
    # Performing our network request and storing the response
    return requests.request("GET", url, params=querystring)


def perform_extra_url_query(url):
    """Performs a request to the URL supplied

    Arguments:
        url {string} -- A URL directing to another page of results from the NASA API

    Returns:
        Response object -- The response received from the NASA API
    """

    return requests.request("GET", url)


def check_query_was_successful(response):
    """Checks if the response status code was anythin except for 200,
    meaning our query failed and there is an issue

    Arguments:
        response {Response object} -- The response from the NASA API
    """

    # Checking to see that our request was successful
    if response.status_code != 200:
        print("Request failed, please check your internet connection")
        sys.exit()


def check_query_for_results(data):
    """Checks that the API query result returned more than 0 results to make
    sure we have data to work with

    Arguments:
        data {Dictionary} -- A python dictionary containing the converted JSON data received from the API
    """

    # Checking that our request returned actual results
    if data["collection"]["metadata"]["total_hits"] == 0:
        print("0 results were returned from query, please check your query")
        sys.exit()


def generate_items_array_from_data(data, totalItemsNumber):
    """Iterates through all result pages returned from the NASA API and
    generates an array of item object, the function will check for extra result
    pages and add the results from those pages to the final array as well

    Arguments:
        data {Dictionary} -- A python dictionary containing the converted JSON data received from the API
        totalItemsNumber {[integer]} -- The total number of results returned from the NASA API

    Returns:
        list -- A list containing all media results returned from the NASA API
    """

    items = data["collection"]["items"]

    if len(items) != totalItemsNumber:
        # The number of items received from the result is not the total number
        # of results, meaning there are more result pages
        while(len(items) != totalItemsNumber):
            # Checking if there are more result pages
            for link in data["collection"]["links"]:
                # Checking if the result page is for a new result page or one
                # we queried before
                if link["rel"] == "next":
                    # The result page is one we didn't query yet, getting data
                    response = perform_extra_url_query(link["href"])
                    data = json.loads(response.text)
                    # Adding results from new page to our total results list
                    items += data["collection"]["items"]
    return items


def generate_final_array_from_items(items):
    """Receives the list of item results retrieved from the API and checks the
    file for images larger than 1000kb and stores their IDs and sizes in a list

    The query is performed by checking the metadata.json file every image in
    the API has and checking for the file size listed

    Arguments:
        items {list} -- A list of item results retrieved from the API

    Returns:
        list -- A list of dictionaries containing NASA IDs and file sizes for
        images larger than 1000kb
    """

    # Creating empty list for results
    finalArr = list()
    nasaID = ""
    for image in items:
        # Querying the data object in every result to check that the media
        # type is an image
        for dataObj in image["data"]:
            if dataObj["media_type"] == "image":
                # Image found, storing NASA ID
                nasaID = dataObj["nasa_id"]
                print(nasaID)
                # Querying the json collection for the image
                response = perform_extra_url_query(image["href"])
                data = json.loads(response.text)
                for item in data:
                    # Checking that the image has a corresponding metadata
                    # document to extract file size from
                    if "metadata.json" in item:
                        response = perform_extra_url_query(item)
                        # Getting image metadata from metadata file
                        imageMetadata = json.loads(response.text)
                        # Checking that metadata file lists a FileSize property
                        if "File:FileSize" in imageMetadata:
                            imageSize = imageMetadata["File:FileSize"]
                            # Checking if file size is listed in kB and is
                            # larger than 1000
                            if "kB" in imageSize and int(imageSize.split(" ")[0]) > 1000:
                                # File larger than 1000 kB, saving in array
                                finalArr.append(
                                    {"Nasa_id": nasaID, "kb": imageSize.split(" ")[0]})
                            # Checking if file size is listed in MB and is
                            # larger than 1000 kB
                            elif "MB" in imageSize and int(float(imageSize.split(" ")[0])*1000) > 1000:
                                # File larger than 1000 kb, saving in array
                                finalArr.append(
                                    {"Nasa_id": nasaID, "kb": int(float(imageSize.split(" ")[0])*1000)})
    # Returning the finished result array
    return finalArr


def generate_csv_file_from_final_array(finalArr):
    """Writes a CSV file containing the results from the NASA API

    Arguments:
        finalArr {list} -- An array containing dictionaries of NASA IDs and file sizes
    """

    with open('nasa_ids.csv', 'w', newline='') as csvFile:
        fieldnames = ['Nasa_id', "kb"]
        writer = csv.DictWriter(csvFile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(finalArr)


def main():
    """Main script function
    """

    response = perform_nasa_api_query("Ilan Ramon")

    check_query_was_successful(response)

    # Storing the response text as JSON for easy manipulation and further querying
    data = json.loads(response.text)

    check_query_for_results(data)

    totalItemsNumber = data["collection"]["metadata"]["total_hits"]

    print("Total number of items from query: {0}".format(totalItemsNumber))

    items = generate_items_array_from_data(data, totalItemsNumber)
    # check_for_more_result_pages(data)
    # Storing image results in a JSON object array
    print("Number of items in array: {0}".format(len(items)))

    finalArr = generate_final_array_from_items(items)

    generate_csv_file_from_final_array(finalArr)

    print("Finished generating CSV file")


main()
