import telebot
import json
import re

# Create a Telebot instance
bot = telebot.TeleBot("6074675799:AAGorq7Par0IHhUu0C-bnBPs9lKPjOKT8oI")


# Create a dictionary to keep track of the user's search progress
search_progress = {}


# Handle start command and give the user a welcome message
@bot.message_handler(commands=["start"])
def welcome(message):
    user = message.from_user
    message_text = f"Welcome, {user.first_name}! 😊\n\nI'm a file search bot. You can simply send me the name of a series or movie, and I'll check my database for it."

    bot.send_message(chat_id=message.chat.id, text=message_text)


# Load file data from JSON
def load_file_data():
    try:
        with open("file_data.json", "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    return data


# Function to save file information to JSON
def save_file_data(file_data):
    with open("file_data.json", "w") as file:
        json.dump(file_data, file)


# Handle search queries
@bot.message_handler(func=lambda message: True)
def handle_search(message):
    search_query = message.text.lower()

    # Replace commas, underscores, exclamation marks, and full stops with spaces
    search_query = re.sub(r"[,_!\.\-]", " ", search_query)

    # Load file data
    file_data = load_file_data()

    # Search for files based on query
    results = []
    for file_name, file_ids in file_data.items():
        # Replace underscores, dots, and hyphens with spaces in the file name
        normalized_file_name = re.sub(r"[_!\.\-]", " ", file_name.lower())

        # Check if there is a year in the normalized file name
        if re.search(r"\b(19|20)\d{2}\b", normalized_file_name):
            normalized_file_name = re.sub(
                r"\b(19|20)\d{2}\b", " ", normalized_file_name
            )

        # Replace consecutive spaces with a single space if there are more than one
        if "   " in normalized_file_name:
            normalized_file_name = normalized_file_name.replace("   ", " ")

        if "  " in normalized_file_name:
            normalized_file_name = normalized_file_name.replace("  ", " ")

        if search_query in normalized_file_name:
            for file_id in file_ids:
                results.append((file_name, file_id))

    # Sort results based on file name while ignoring special characters and spaces
    results = sorted(results, key=lambda x: re.sub(r"[%!_.\- ]", "", x[0]).lower())

    # Send search results to user
    num_results = len(results)
    try:
        if num_results == 1:
            bot.send_message(
                chat_id=message.chat.id,
                text=f"🔎\t\tSending only one file: ",
            )
        elif num_results == 0:
            bot.send_message(
                chat_id=message.chat.id,
                text=f"🙅‍♂️\t\tSorry '{search_query.title()}' not found!",
            )

        else:
            bot.send_message(
                chat_id=message.chat.id,
                text=f"🔎\t\tSending {num_results} Search Results:",
            )
    except Exception as e:
        print(f"Error: Unable to send search results. {str(e)}")

    # Send file results to user
    if num_results > 0:
        search_progress[message.chat.id] = {
            "results": results,
            "index": 0,
        }  # Store the search results and starting index in the search_progress dictionary
        send_next_files(message.chat.id)


# Send the next 30 files to the user
def send_next_files(chat_id):
    search_data = search_progress.get(chat_id)
    if search_data:
        results = search_data["results"]
        index = search_data["index"]
        num_results = len(results)

        sent_files = 0  # Initialize variable to keep track of sent files

        # Sort results based on modified caption in alphabetical order
        sorted_results = sorted(
            results, key=lambda x: re.sub(r"[%!_.\- ]", "", x[0]).lower()
        )

        for i in range(index, min(index + 30, num_results)):
            file_name, file_id = sorted_results[i]
            try:
                # Modify the caption
                caption = re.sub(r"\s+|[,.\[\]_]", ".", file_name)
                caption = re.sub(
                    r"\.+", ".", caption
                )  # Replace multiple periods with a single period
                caption = caption.strip(".")  # Remove leading/trailing periods

                bot.send_document(chat_id=chat_id, document=file_id, caption=caption)
                sent_files += 1  # Increment variable after each file is sent
            except Exception as e:
                print(f"Error: Unable to send the file. {str(e)}")

        # Update the index in the search_progress dictionary
        search_data["index"] = index + sent_files

        # Check if there are more files to send
        if index + sent_files < num_results:
            # Send continue button
            bot.send_message(
                chat_id=chat_id,
                text="Click 👇 to Continue",
                reply_markup=telebot.types.InlineKeyboardMarkup().add(
                    telebot.types.InlineKeyboardButton("Continue", callback_data="continue")
                ),
            )
        else:
            # All files have been sent, remove search progress for the user
            del search_progress[chat_id]

            # Send the "⚡" message
            bot.send_sticker(
                chat_id=chat_id,
                sticker="CAACAgIAAxkBAAJVOWSy9oCmjaTnAudy8_RpM5cXcmVYAALiBQACP5XMCnNlX6_emGTgHgQ",
            )


# Handle button callback for continuing to send files
@bot.callback_query_handler(func=lambda call: call.data == "continue")
def continue_sending_files(callback_query):
    chat_id = callback_query.message.chat.id

    # Delete the "Continue" message and button
    try:
        bot.delete_message(chat_id=chat_id, message_id=callback_query.message.message_id)
    except Exception as e:
        print(f"Error: Unable to delete the message. {str(e)}")

    # Send the next batch of files
    send_next_files(chat_id)


# Run the bot
try:
    bot.polling()
except Exception as e:
    print(f"Error: Unable to run the bot. {str(e)}")
