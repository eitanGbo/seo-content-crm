import json
import os
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
from datetime import datetime, timedelta

DATA_FILE = 'data.json'

DEFAULT_STATUS = 'Pending Writing'
STATUSES = ['Pending Writing', 'Pending Approval', 'Published']


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {'projects': []}


def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_months():
    months = []
    today = datetime.today().replace(day=1)
    for i in range(12):
        m = today + timedelta(days=31*i)
        months.append(m.strftime('%Y-%m'))
    return months


class ArticleDialog(simpledialog.Dialog):
    def __init__(self, parent, title, article=None):
        self.article = article or {}
        super().__init__(parent, title)

    def body(self, frame):
        tk.Label(frame, text='Title').grid(row=0, column=0, sticky='e')
        tk.Label(frame, text='Keyword').grid(row=1, column=0, sticky='e')
        tk.Label(frame, text='Outbound Anchor').grid(row=2, column=0, sticky='e')
        tk.Label(frame, text='Outbound Target').grid(row=3, column=0, sticky='e')
        tk.Label(frame, text='Inbound Anchor').grid(row=4, column=0, sticky='e')
        tk.Label(frame, text='Inbound Source').grid(row=5, column=0, sticky='e')
        tk.Label(frame, text='Month').grid(row=6, column=0, sticky='e')
        tk.Label(frame, text='Status').grid(row=7, column=0, sticky='e')

        self.title_var = tk.Entry(frame)
        self.keyword_var = tk.Entry(frame)
        self.out_anchor_var = tk.Entry(frame)
        self.out_target_var = tk.Entry(frame)
        self.in_anchor_var = tk.Entry(frame)
        self.in_source_var = tk.Entry(frame)
        self.month_var = ttk.Combobox(frame, values=get_months())
        self.status_var = ttk.Combobox(frame, values=STATUSES)

        self.title_var.grid(row=0, column=1)
        self.keyword_var.grid(row=1, column=1)
        self.out_anchor_var.grid(row=2, column=1)
        self.out_target_var.grid(row=3, column=1)
        self.in_anchor_var.grid(row=4, column=1)
        self.in_source_var.grid(row=5, column=1)
        self.month_var.grid(row=6, column=1)
        self.status_var.grid(row=7, column=1)

        # prefill
        self.title_var.insert(0, self.article.get('title', ''))
        self.keyword_var.insert(0, self.article.get('keyword', ''))
        self.out_anchor_var.insert(0, self.article.get('out_anchor', ''))
        self.out_target_var.insert(0, self.article.get('out_target', ''))
        self.in_anchor_var.insert(0, self.article.get('in_anchor', ''))
        self.in_source_var.insert(0, self.article.get('in_source', ''))
        self.month_var.set(self.article.get('month', get_months()[0]))
        self.status_var.set(self.article.get('status', DEFAULT_STATUS))

    def apply(self):
        self.result = {
            'title': self.title_var.get(),
            'keyword': self.keyword_var.get(),
            'out_anchor': self.out_anchor_var.get(),
            'out_target': self.out_target_var.get(),
            'in_anchor': self.in_anchor_var.get(),
            'in_source': self.in_source_var.get(),
            'month': self.month_var.get(),
            'status': self.status_var.get() or DEFAULT_STATUS,
        }


class ProjectWindow(tk.Toplevel):
    def __init__(self, master, project):
        super().__init__(master)
        self.project = project
        self.title(project['name'])
        self.geometry('700x500')

        months = get_months()
        self.tabs = ttk.Notebook(self)
        self.tab_frames = {}
        for m in months:
            frame = tk.Frame(self.tabs)
            self.tabs.add(frame, text=m)
            self.tab_frames[m] = frame
            self._build_month(frame, m)
        self.tabs.pack(fill='both', expand=True)

        tk.Button(self, text='Add Article', command=self.add_article).pack(side='left')
        tk.Button(self, text='Export JSON', command=self.export_json).pack(side='left')
        tk.Button(self, text='Export CSV', command=self.export_csv).pack(side='left')

    def _build_month(self, frame, month):
        cols = ('Title', 'Status')
        tree = ttk.Treeview(frame, columns=cols, show='headings')
        for c in cols:
            tree.heading(c, text=c)
        tree.pack(fill='both', expand=True)
        frame.tree = tree
        self.refresh_month(month)
        tree.bind('<Double-1>', lambda e, m=month: self.edit_selected(m))

    def refresh_month(self, month):
        frame = self.tab_frames[month]
        tree = frame.tree
        for i in tree.get_children():
            tree.delete(i)
        for idx, art in enumerate(self.project.get('articles', [])):
            if art.get('month') == month:
                tree.insert('', 'end', iid=str(idx), values=(art['title'], art['status']))

    def add_article(self):
        dlg = ArticleDialog(self, 'Add Article')
        if dlg.result:
            self.project.setdefault('articles', []).append(dlg.result)
            save_data(app.data)
            self.refresh_month(dlg.result['month'])

    def edit_selected(self, month):
        frame = self.tab_frames[month]
        tree = frame.tree
        item = tree.focus()
        if not item:
            return
        idx = int(item)
        art = self.project['articles'][idx]
        dlg = ArticleDialog(self, 'Edit Article', art)
        if dlg.result:
            self.project['articles'][idx] = dlg.result
            save_data(app.data)
            self.refresh_month(month)

    def export_json(self):
        path = filedialog.asksaveasfilename(defaultextension='.json')
        if path:
            with open(path, 'w') as f:
                json.dump(self.project, f, indent=2)

    def export_csv(self):
        import csv
        path = filedialog.asksaveasfilename(defaultextension='.csv')
        if path:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Title', 'Keyword', 'Outbound Anchor', 'Outbound Target',
                                 'Inbound Anchor', 'Inbound Source', 'Month', 'Status'])
                for art in self.project.get('articles', []):
                    writer.writerow([
                        art.get('title', ''),
                        art.get('keyword', ''),
                        art.get('out_anchor', ''),
                        art.get('out_target', ''),
                        art.get('in_anchor', ''),
                        art.get('in_source', ''),
                        art.get('month', ''),
                        art.get('status', '')
                    ])

class App(tk.Tk):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.title('SEO Content CRM')
        self.geometry('400x300')

        self.project_list = tk.Listbox(self)
        self.project_list.pack(fill='both', expand=True)

        btn_frame = tk.Frame(self)
        btn_frame.pack()
        tk.Button(btn_frame, text='Add Project', command=self.add_project).pack(side='left')
        tk.Button(btn_frame, text='Rename', command=self.rename_project).pack(side='left')
        tk.Button(btn_frame, text='Delete', command=self.delete_project).pack(side='left')
        tk.Button(btn_frame, text='Open', command=self.open_project).pack(side='left')

        self.refresh_projects()

    def refresh_projects(self):
        self.project_list.delete(0, tk.END)
        for p in self.data.get('projects', []):
            self.project_list.insert(tk.END, p['name'])

    def add_project(self):
        name = simpledialog.askstring('Project Name', 'Enter project domain:')
        if name:
            self.data['projects'].append({'name': name, 'articles': []})
            save_data(self.data)
            self.refresh_projects()

    def rename_project(self):
        sel = self.project_list.curselection()
        if not sel:
            return
        idx = sel[0]
        project = self.data['projects'][idx]
        new = simpledialog.askstring('Rename Project', 'New name:', initialvalue=project['name'])
        if new:
            project['name'] = new
            save_data(self.data)
            self.refresh_projects()

    def delete_project(self):
        sel = self.project_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if messagebox.askyesno('Delete', 'Are you sure?'):
            self.data['projects'].pop(idx)
            save_data(self.data)
            self.refresh_projects()

    def open_project(self):
        sel = self.project_list.curselection()
        if not sel:
            return
        idx = sel[0]
        proj = self.data['projects'][idx]
        ProjectWindow(self, proj)

if __name__ == '__main__':
    data = load_data()
    app = App(data)
    app.mainloop()
    save_data(app.data)
