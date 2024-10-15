Style Guide for Fahrverein Planetal e.V. Website

General Guidelines

This style guide defines the design standards to ensure consistency across all pages of the Fahrverein Planetal e.V. website. The website uses TailwindCSS and Flowbite for its styling, with specific considerations for colors, typography, spacing, and layout components.

Color Palette

The website follows a light/dark theme switchable color palette:

Primary Colors:

Light Theme Background: bg-slate-50

Dark Theme Background: dark:bg-gray-900

Accent Color: bg-white, text-gray-900

Dark Text: dark:text-white

Text Colors:

Headings: text-gray-900 (light theme), dark:text-white (dark theme)

Paragraphs: text-gray-500 (light theme), dark:text-gray-400 (dark theme)

Links: text-gray-700 (default), hover:text-black, dark:text-gray-400, md:dark:hover:text-white

Footer Text: text-gray-400 (light theme), hover:text-white (dark theme)

Borders & Dividers:

Borders: border-gray-200 (light theme), dark:border-gray-700 (dark theme)

Divider Lines (in footer and navigation): border-gray-600

Typography

The typography is focused on readability and a clean, modern appearance.

Headings:

Use the .font-extrabold and .text-4xl classes for major headings (e.g., welcome messages on the index page).

Heading sizes should adapt to the screen size using Tailwind's responsive classes: md:text-5xl, lg:text-6xl.

Body Text:

Use .text-lg for standard text in sections and .font-normal to maintain consistency.

Paragraphs should use text-gray-500 for a less intense visual load.

Navigation Text:

Links within the navigation bar use .text-gray-700 with a hover effect that changes to .hover:bg-gray-100 in the light theme and .md:hover:text-black for dark theme.

Spacing and Layout

Spacing helps maintain consistency and provides an organized structure to the pages.

Sections:

Padding and margin classes such as py-8, px-4, and mx-auto are used to define spacing between sections and align the content centrally.

Containers:

The maximum container width for main sections is max-w-screen-xl.

The footer and navigation utilize container mx-auto to centrally align the content.

Utility Classes:

Use .flex, .flex-wrap, and .justify-between to maintain the layout structure for navigation and footer elements.

Conditional styling based on screen size is essential, e.g., md:flex-row and lg:py-16 for responsive designs.

Components

Navigation Bar:

The navigation bar (nav.html) uses a combination of .bg-white and .dark:bg-gray-900 for light and dark themes, respectively.

Include a toggle button (data-collapse-toggle) for smaller screens with md:hidden to hide it on larger screens.

Navigation links should use hover transitions: .hover:bg-gray-100 for light themes and .dark:hover:bg-gray-700 for dark themes.

Footer:

The footer (footer.html) follows a dark background (bg-gray-800) and uses text-gray-400 for the non-emphasized text.

Links in the footer should have a hover effect that changes their color to hover:text-white.

Vertical and horizontal dividers (border-l and border-t) should be applied to separate content visually.

Authentication Messages:

For conditional user messages (index.html), use .text-4xl for welcoming text and adapt its size based on user state.

Ensure the messages for authenticated users (current_user) and non-authenticated users are distinguishable by adapting the welcome message accordingly.

Personalization Ideas

To make the website more personalized and reflective of the Fahrverein Planetal e.V. community, consider the following additions:

Fonts:

Use a modern and elegant font such as "Poppins" or "Roboto" to give a clean yet warm feel to the website. These fonts are easy to read and suitable for both headings and body text.

Imagery and Icons:

Include imagery that reflects the club's activities, such as photos of horses, events, and members. Utilize .object-cover to ensure images look visually pleasing across different devices.

Use horse-themed icons or illustrations where applicable, such as next to navigation links or in section headers, to enhance visual interest and relevance.

Mobile Responsiveness:

Ensure all pages are optimized for mobile use, with special attention to button sizes (.py-2, .px-4), readability (.text-base on mobile), and navigation (data-collapse-toggle for menus).

Modern and Simple Layout:

Stick to a minimalist layout, using generous white space (.mx-auto, .my-8) to keep the focus on the content. Components like cards (.shadow-lg, .rounded-lg) should be used to group related content while maintaining a clean look.

Emphasize important call-to-action buttons by using standout colors like bg-blue-600 with hover:bg-blue-700 for better visibility.

User Profiles:

Create member profile pages where users can see their participation in events, horses they own, and community achievements. Use .flex and .gap-4 to layout profile details and images neatly.

Internal Members-Only Area:

Develop a members-only area accessible only after authentication. This section could include:

Internal Blog: Updates and announcements about club activities, events, and members-only resources.

Community Forum: A simple forum where members can discuss topics related to horse riding, training, and events.

Event Calendar: An interactive calendar (.bg-white, .shadow-md) that shows upcoming events, available only to members.

Additional Pages

Blog Pages:

Use .prose classes for blog content to make reading enjoyable and to keep styling consistent. Add a featured image to each blog post, and ensure the layout remains responsive (.sm:px-6, .lg:px-12).

Add a comments section at the bottom of each post, allowing registered users to interact.

Contact Page:

Include a contact form (.bg-white, .rounded-lg, .shadow-lg) with fields for name, email, subject, and message. Use .focus:ring-blue-500 for input fields to make them stand out during interaction.

Add a map showing the club's location using an embedded map component to give a personal touch.

About Us Page:

Use a split layout (.grid, .md:grid-cols-2, .gap-8) to tell the club's story on one side and showcase images on the other. Highlight the club's mission, history, and key achievements.

Include testimonials from members to provide authenticity and build trust.

Form Pages:

Use .space-y-4 to add vertical spacing between form fields, making them easy to interact with. Include a progress indicator if the form is multi-step.

Provide feedback messages (.text-green-500 for success, .text-red-500 for errors) to guide users through the process.

Profile Pages:

Member profile pages can include .tabs for different sections such as "My Events," "My Horses," and "My Achievements." Include profile pictures (.rounded-full, .border) to add a personal touch.

SEO and Accessibility Improvements

Search Engine Optimization (SEO):

Meta Tags: Ensure each page has appropriate meta tags, including title, description, and keywords to improve search engine visibility.

URL Structure: Use clean and descriptive URLs (/about-us, /contact) that are easy to read and relevant to the content.

Alt Attributes: Add descriptive alt attributes to all images to help search engines understand the content and to improve accessibility for screen readers.

Sitemap: Create an XML sitemap and submit it to search engines to ensure all pages are indexed.

Social Media Metadata: Use Open Graph and Twitter Card metadata to make shared links more attractive on social media platforms.

Accessibility:

ARIA Roles: Use ARIA (Accessible Rich Internet Applications) roles where applicable to provide additional context to assistive technologies.

Keyboard Navigation: Ensure all interactive elements can be accessed via keyboard. Use :focus styles to indicate focus for users navigating with the keyboard.

Color Contrast: Ensure sufficient contrast between text and background colors to meet WCAG AA standards, making the website more accessible to visually impaired users.

Semantic HTML: Use semantic HTML elements (<header>, <nav>, <main>, <footer>) to improve the document structure and help assistive technologies better understand the content.

Skip to Content Link: Add a "Skip to Content" link at the top of each page to help users with screen readers or those navigating via keyboard to skip repetitive navigation links.

Best Practices

Use of CDN: TailwindCSS and Flowbite are linked via CDN, reducing initial setup but might require caution regarding offline availability and potential breaking changes.

Responsive Design: Utilize Tailwind's responsive classes (md:, lg:) to create an adaptive and user-friendly experience across different devices.

Dark Mode Support: Always include a dark mode variant (dark: prefix) to ensure consistent visual quality for users who prefer dark themes.

Icon Usage: Use SVGs for icons (e.g., menu open icon) to ensure scalability and clear visuals on high-resolution displays.

Additional Notes

Consistency is key: maintain the same classes for similar elements across pages to ensure uniformity.

Ensure links are clearly visible and have appropriate contrast to meet accessibility standards (e.g., WCAG AA).