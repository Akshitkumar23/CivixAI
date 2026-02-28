import sys
import os

file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'app', 'check-eligibility', 'page.tsx')
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix annualIncome check
content = content.replace('if (formData.annualIncome)', 'if (formData.annualIncome !== undefined && formData.annualIncome !== null)')
# Fix age check
content = content.replace('if (formData.age)', 'if (formData.age !== undefined && formData.age !== null)')
# Fix success UI
old_success = '''                  {eligibleSchemes.length > 0 ? (
                    <div className="space-y-3">
                      {eligibleSchemes.map((scheme, index) => (
                        <div key={index} className="flex items-center justify-between p-4 border rounded-lg bg-green-50/50">
                          <div className="flex items-center gap-3">
                            <CheckCircle className="h-5 w-5 text-green-600" />
                            <span className="font-medium">{scheme}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : ('''

new_success = '''                  {eligibleSchemes.length > 0 ? (
                    <div className="space-y-4">
                      <div className="bg-primary/5 p-4 rounded-2xl border border-primary/20 text-left">
                        <div className="flex items-center gap-2 text-primary font-black mb-1 uppercase tracking-tighter text-sm">
                          <span className="flex items-center gap-1"><CheckCircle className="h-4 w-4" /> Smart Matches</span>
                        </div>
                        <div className="space-y-2 mt-3">
                          {eligibleSchemes.slice(0, 5).map((scheme, index) => (
                            <div key={index} className="flex items-center gap-3 p-3 bg-white border rounded-xl shadow-sm">
                              <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center text-green-700 font-bold text-xs shrink-0">{index + 1}</div>
                              <span className="font-bold text-sm line-clamp-1">{scheme}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground">AI ne total <strong>{eligibleSchemes.length}</strong> matches dhoondhe hain.</p>
                    </div>
                  ) : ('''

content = content.replace(old_success, new_success)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
