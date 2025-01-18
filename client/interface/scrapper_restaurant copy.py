import streamlit as st


def show():
    st.text_input("Enter the restaurant URL", key="restaurant_url")
    if st.button("Scrape"):
        url = st.session_state.restaurant_url
        if url:
            with st.spinner("Scraping in progress..."):
                try:
                    # Call the scraping API on the server
                    response = requests.post("http://server/scraper", json={"url": url})
                    response.raise_for_status()
                    data = response.json()
                    st.success("Scraping completed successfully!")
                    st.json(data)
                    
                    # Display additional structured data
                    st.subheader("Restaurant Details")
                    st.write(f"Name: {data.get('name', 'N/A')}")
                    st.write(f"Address: {data.get('address', 'N/A')}")
                    st.write(f"Rating: {data.get('rating', 'N/A')}")
                    st.write(f"Reviews: {data.get('reviews', 'N/A')}")
                    
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to scrape the restaurant: {e}")
        else:
            st.warning("Please enter a valid URL.")
    st.title("Scrapper Restaurant")