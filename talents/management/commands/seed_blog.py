from django.core.management.base import BaseCommand
from talents.models import BlogPost

class Command(BaseCommand):
    help = 'Adds 3 sample blog posts'

    def handle(self, *args, **kwargs):
        posts = [
            {
                "title": "How to build a perfect portfolio",
                "category": "Tips",
                "image": "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                "excerpt": "Learn the secrets to attracting high-paying clients with a clean profile.",
                "content": """Your portfolio is your most powerful marketing tool. In the digital age, clients spend less than 10 seconds deciding if they want to hire you. Here is how to make those seconds count.

1. Show, Don't Just Tell
Instead of listing "Java" as a skill, show a project where you used Java to solve a complex problem. Use screenshots, links to live demos, and GitHub repositories.

2. Quality Over Quantity
It is better to have 3 amazing projects than 10 mediocre ones. Curate your best work. If a project is old or doesn't represent your current skill level, remove it.

3. Write Case Studies
For your top projects, write a short case study. Explain the problem, your specific role, the tools you used, and the final outcome. Clients love to see your thought process.

4. Keep it Updated
An outdated portfolio is a red flag. Make sure your contact information is current and your latest work is visible at the top."""
            },
            {
                "title": "TalentHub hits 500 Verified Users",
                "category": "News",
                "image": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                "excerpt": "We are celebrating a major milestone in our journey to connect talent.",
                "content": """We are thrilled to announce that TalentHub has officially crossed 500 verified professionals on our platform! 

This milestone represents more than just a number; it represents 500 individual careers we are helping to grow. From graphic designers in Lagos to software engineers in Abuja, our community is diverse and rapidly expanding.

Why Verification Matters
Our strict verification process is what sets us apart. We don't just let anyone join; we ensure every talent has proven skills. This builds trust with employers and ensures high-quality deliverables.

What's Next?
We are launching new features next month, including direct payments and project management tools. Stay tuned!"""
            },
            {
                "title": "The Future of Remote Work",
                "category": "Community",
                "image": "https://images.unsplash.com/photo-1552664730-d307ca884978?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                "excerpt": "Why more companies in Nigeria are switching to hybrid work models.",
                "content": """Remote work is no longer a temporary fix; it is a permanent shift in how we operate. Companies across Nigeria and the globe are realizing that talent is not restricted by geography.

The Hybrid Model
Most companies are settling into a hybrid model—2 days in the office, 3 days at home. This offers the best of both worlds: the collaboration of in-person meetings and the flexibility of remote work.

Tools You Need
To succeed in this new environment, you need to master tools like Slack, Zoom, Jira, and Notion. Communication skills are now just as important as technical skills.

At TalentHub, we are committed to supporting this shift by connecting remote-ready talent with forward-thinking companies."""
            }
        ]

        for p in posts:
            BlogPost.objects.create(
                title=p['title'],
                category=p['category'],
                image_url=p['image'],
                excerpt=p['excerpt'],
                content=p['content']
            )
            self.stdout.write(self.style.SUCCESS(f"Created post: {p['title']}"))