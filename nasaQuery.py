import csv
import json
import sys
import requests


def perform_nasa_api_query(search_term):
    """Receives a search term and queries the nasa image and video library API for results

    Arguments:
        searchTerm {string} -- The term to search for in the API

    Returns:
        Response object -- The response received from the NASA API
    """

    # Storing API search URL in variable
    url = "https://images-api.nasa.gov/search"
    query_string = {"q": search_term}
    # Performing our network request and storing the response
    response = requests.request("GET", url, params=query_string)
    check_query_was_successful(response)
    return response


def perform_extra_url_query(url):
    """Performs a request to the URL supplied

    Arguments:
        url {string} -- A URL directing to another page of results from the NASA API

    Returns:
        Response object -- The response received from the NASA API
    """

    response = requests.request("GET", url)
    check_query_was_successful(response)
    return response


def check_query_was_successful(response):
    """Checks if the response status code was anythin except for 200,
    meaning our query failed and there is an issue

    Arguments:
        response {Response object} -- The response from the NASA API
    """

    # Checking to see that our request was successful
    if response.status_code != 200:
        print("Status code is not 200, exiting")
        sys.exit()


def check_query_for_results(data):
    """Checks that the API query result returned more than 0 results to make
    sure we have data to work with

    Arguments:
        data {Dictionary} -- A python dictionary containing the converted JSON data received from the API

    Returns:
        integer -- The number of results the API found
    """

    # Checking that our request returned actual results
    if data["collection"]["metadata"]["total_hits"] == 0:
        print("0 results were returned from query, please check your query")
        sys.exit()
    return data["collection"]["metadata"]["total_hits"]


def generate_items_array_from_data(data, total_items):
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
    # The number of items received from the result is not the total number
    # of results, meaning there are more result pages
    while(len(items) != total_items):
        # Checking if there are more result pages
        for link in data["collection"]["links"]:
            # Checking if the result page is for a new result page or one
            # we queried before
            if link["rel"] == "next":
                # The result page is one we didn't query yet, getting data
                next_page_response = perform_extra_url_query(link["href"])
                data = json.loads(next_page_response.text)
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
    final_entries = []
    nasa_id = ''
    for image in items:
        # Querying the data object in every result to check that the media
        # type is an image
        for data_obj in image["data"]:
            if data_obj["media_type"] != "image":
                # Image not found, skipping
                pass
            nasa_id = data_obj["nasa_id"]
            print(nasa_id)
            # Querying the json collection for the image
            image_versions_response = perform_extra_url_query(image["href"])
            data = json.loads(image_versions_response.text)
            for item in data:
                # Checking that the image has a corresponding metadata
                # document to extract file size from
                if "metadata.json" in item:
                    csv_entry = get_image_metadata(
                        item, final_entries, nasa_id)
                    if csv_entry is not None:
                        final_entries.append(csv_entry)

    return final_entries


def get_image_metadata(item, final_entries, nasa_id):
    image_versions_response = perform_extra_url_query(item)
    # Getting image metadata from metadata file
    imageMetadata = json.loads(image_versions_response.text)
    # Checking that metadata file lists a FileSize property
    if "File:FileSize" in imageMetadata:
        # image_raw_size is the size represented with a unit (i.e kb/mb...)
        image_raw_size = imageMetadata["File:FileSize"]
        return check_image_size(image_raw_size, final_entries, nasa_id)


def check_image_size(image_raw_size, final_entries, nasa_id):
    # Checking if file size is listed in kB and is larger than 1000 kB
    if "kB" in image_raw_size:
        image_size = int(image_raw_size.split(" ")[0])
        if image_size > 1000:
            # File larger than 1000 kB, saving in array
            return {"Nasa_id": nasa_id, "kb": image_size}
    # Checking if file size is listed in MB and is larger than 1000 kB
    elif "MB" in image_raw_size:
        image_size = int(float(image_raw_size.split(" ")[0])*1000)
        if image_size > 1000:
            # File larger than 1000 kb, saving in array
            return {"Nasa_id": nasa_id, "kb": image_size}


def generate_csv_file_from_final_array(final_entries):
    """Writes a CSV file containing the results from the NASA API

    Arguments:
        finalArr {list} -- An array containing dictionaries of NASA IDs and file sizes
    """

    with open('nasa_ids.csv', 'w', newline='') as csv_file:
        field_names = ['Nasa_id', "kb"]
        writer = csv.DictWriter(csv_file, fieldnames=field_names)

        writer.writeheader()
        writer.writerows(final_entries)


def main():
    """Main script function
    """

    initial_api_response = perform_nasa_api_query("Ilan Ramon")

    # Storing the response text as JSON for easy manipulation and further querying
    data = json.loads(initial_api_response.text)

    totalItemsNumber = check_query_for_results(data)

    print("Total number of items from query: {0}".format(totalItemsNumber))

    items = generate_items_array_from_data(data, totalItemsNumber)
    # Storing image results in a JSON object array
    print("Number of items in array: {0}".format(len(items)))

    final_entries = generate_final_array_from_items(items)

    generate_csv_file_from_final_array(final_entries)

    print("Finished generating CSV file")


if __name__ == "__main__":
    main()
